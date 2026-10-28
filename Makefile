# These can be overidden with env vars.
REGISTRY ?= localhost:5001
IMAGE_NAME ?= promotions
IMAGE_TAG ?= 1.0
IMAGE ?= $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
PLATFORM ?= "linux/amd64,linux/arm64"
CLUSTER ?= nyu-devops
KUBE_CONTEXT ?= k3d-$(CLUSTER)
KUBECTL = kubectl --context $(KUBE_CONTEXT)

.SILENT:

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: all
all: help

##@ Development

.PHONY: clean
clean:	## Removes all dangling build cache
	$(info Removing all dangling build cache..)
	-docker rmi $(IMAGE)
	docker image prune -f
	docker buildx prune -f

.PHONY: install
install: ## Install Python dependencies
	$(info Installing dependencies...)
	sudo pipenv install --system --dev

.PHONY: lint
lint: ## Run the linter
	$(info Running linting...)
	flake8 service tests --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 service tests --count --max-complexity=10 --max-line-length=127 --statistics
	pylint service tests --max-line-length=127

.PHONY: test
test: ## Run the unit tests
	$(info Running tests...)
	export RETRY_COUNT=1; pytest --pspec --cov=service --cov-report=xml --cov-fail-under=95 --disable-warnings


.PHONY: run
run: ## Run the service
	$(info Starting service...)
	honcho start

.PHONY: secret
secret: ## Generate a secret hex key
	$(info Generating a new secret key...)
	python3 -c 'import secrets; print(secrets.token_hex())'

##@ Kubernetes

.PHONY: cluster
cluster: ## Create a K3D Kubernetes cluster with load balancer and registry
	$(info Creating Kubernetes cluster $(CLUSTER) with a registry and 1 worker nodes...)
	@docker inspect k3d-cluster-registry >/dev/null 2>&1 || k3d registry create cluster-registry --port 127.0.0.1:5001
	k3d cluster create $(CLUSTER) --agents 1 --registry-use k3d-cluster-registry:5000 --registry-config ./config/registries.yaml --port '127.0.0.1:8080:80@loadbalancer' --timeout 180s

.PHONY: cluster-rm
cluster-rm: ## Remove a K3D Kubernetes cluster
	$(info Removing Kubernetes cluster...)
	k3d cluster delete $(CLUSTER)

.PHONY: import
import: ## Import the image into the local K3D cluster
	$(info Importing $(IMAGE) into k3d cluster $(CLUSTER)...)
	k3d image import --cluster $(CLUSTER) $(IMAGE)

.PHONY: deploy
deploy: ## Deploy the service on local Kubernetes
	$(info Deploying service locally...)
	$(KUBECTL) apply -f k8s/namespace.yaml
	$(KUBECTL) apply -f k8s/postgres/
	$(KUBECTL) -n promotions rollout status statefulset/postgres --timeout=180s
	$(KUBECTL) apply -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/ingress.yaml
	$(KUBECTL) -n promotions set image deployment/promotions promotions=$(IMAGE)
	$(KUBECTL) -n promotions rollout restart deployment/promotions
	$(KUBECTL) -n promotions rollout status deployment/promotions --timeout=180s

############################################################
# COMMANDS FOR BUILDING THE IMAGE
############################################################

##@ Image Build and Push

.PHONY: init
init: export DOCKER_BUILDKIT=1
init:	## Creates the buildx instance
	$(info Initializing Builder...)
	-docker buildx create --use --name=qemu
	docker buildx inspect --bootstrap

.PHONY: build
build:	## Build the project container image for local platform
	$(info Building $(IMAGE)...)
	docker build --rm --pull --tag $(IMAGE) .

.PHONY: push
push:	## Push the image to the container registry
	$(info Pushing $(IMAGE)...)
	docker push $(IMAGE)

.PHONY: buildx
buildx:	## Build multi-platform image with buildx
	$(info Building multi-platform image $(IMAGE) for $(PLATFORM)...)
	docker buildx build --file Dockerfile --pull --platform=$(PLATFORM) --tag $(IMAGE) --push .

.PHONY: remove
remove:	## Stop and remove the buildx builder
	$(info Stopping and removing the builder image...)
	docker buildx stop
	docker buildx rm

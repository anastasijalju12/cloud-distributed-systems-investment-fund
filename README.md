# Investment Fund Management System

A project I built for the **IEP** course (2025/26). It's a backend for an investment fund. Employees propose what the fund should buy or sell, and each proposal is decided by a vote through an Ethereum smart contract. The system is split into microservices and runs on Kubernetes.

It passes the full automated test suite from the course (180/180 tests, and 179/179 with blockchain voting enabled).

## What it does

**Users**
- registration and login; after logging in, the user gets a JWT that's valid for one hour
- two roles: director and employee (the director account is created automatically on first startup)
- deleting your own account

**Employees**
- search assets by name, category, and buying/selling date
- filter by an asset's extra info (the `info` field has no fixed structure, so filters are given as a path + Mongo operator + value, e.g. `location.city` `$eq` `"Belgrade"`)
- propose buying a new asset or selling an existing one (proposals wait in Redis until a decision is made)

**Director**
- view all pending proposals
- start a vote on a proposal
- per-category report showing how much was spent and how much was earned (computed with an aggregation pipeline directly in MongoDB: `$unwind` on categories, then `$group`)

**Blockchain voting**
- a separate smart contract with a list of voters is deployed for each proposal
- only addresses on the list can vote, and only once
- the number of voters must be odd, and a proposal passes or fails once one side reaches a majority (n / 2 + 1)
- the contract is compiled when the director service starts, and a background thread watches the deployed contracts for the voting result
- when voting ends, the proposal is removed from Redis, and if it was approved, it's written to MongoDB
- Ganache is used as the local blockchain

## Architecture

| Service | What it does | Uses | Address |
|---|---|---|---|
| `authentication` | registration, login, account deletion | MySQL | `http://127.0.0.1:30000` |
| `employee` | search and proposals (3 replicas) | MongoDB, Redis | `http://127.0.0.1:30001` |
| `director` | decisions, voting, reports | MongoDB, Redis, Ganache | `http://127.0.0.1:30002` |
| `ganache` | local Ethereum blockchain | | `http://127.0.0.1:30003` |

Configuration (service addresses, database names, etc.) is passed through a ConfigMap, and passwords and keys through a Secret. MySQL and MongoDB use PersistentVolumes, so data survives pod restarts.

**Where the data lives**

- MySQL, database `fund`, table `users`: `id`, `forename`, `surname`, `email` (unique), `password`, `role` (`employee` or `director`)
- MongoDB, database `investment_fund`, collection `assets`: `name`, `categories`, `buying_price`, `buying_date`, `info`, plus `selling_price` and `selling_date` once the asset is sold
- Redis: pending proposals, stored as JSON under a UUID key

The JWT contains the user's info from registration (without the password) and their role in the `role` claim.

## Tech stack

Python 3.12, Flask, Flask-JWT-Extended, SQLAlchemy, PyMongo, Redis, MongoDB, MySQL 8, Solidity, web3.py, py-solc-x, Ganache, Docker, Kubernetes (kind)

## Project structure

```
authentication/      user account service
employee/            employee service
director/            director service + smart contract
kubernetes/
  system.yaml        Kubernetes manifest for the whole system
docker-compose.yaml  builds the three service images
databases.yaml       MySQL, MongoDB and Redis (Docker Compose)
kind-config.yaml     kind cluster configuration
pyproject.toml
```

## Running

**Requirements:** Docker Desktop (running), kubectl and kind. The commands below are for PowerShell on Windows and are run from the project root.

### First run

**1. Install kind** (skip if `kind version` already works; run PowerShell as administrator)

```powershell
curl.exe -Lo kind.exe https://kind.sigs.k8s.io/dl/v0.23.0/kind-windows-amd64
Move-Item .\kind.exe C:\Windows\System32\kind.exe
```

**2. Create the cluster**

```powershell
kind create cluster --name fund --config kind-config.yaml
```

**3. Pull the database and blockchain images**

```powershell
docker pull mysql:8.0
docker pull mongo:7
docker pull redis:7
docker pull trufflesuite/ganache-cli
```

**4. Build the service images**

```powershell
$env:BUILDX_NO_DEFAULT_ATTESTATIONS="1"
docker compose build
```

Without `BUILDX_NO_DEFAULT_ATTESTATIONS`, Docker adds attestation manifests to the images, and `kind load` can fail on them.

**5. Load the images into the cluster**

```powershell
kind load docker-image investment-fund-authentication:k8s --name fund
kind load docker-image investment-fund-employee:k8s --name fund
kind load docker-image investment-fund-director:k8s --name fund
kind load docker-image trufflesuite/ganache-cli --name fund
```

**6. Start the databases**

```powershell
docker compose -f databases.yaml up -d
```

**7. Apply the manifest**

```powershell
kubectl apply -f kubernetes/system.yaml
kubectl get pods
```

Steps 3 and 4 need an internet connection: about 1.5 GB for the base images and about 500 MB more for the build (Python base image and pip packages). After that, everything runs offline.

### If the cluster already exists

Check with `kind get clusters` (it should list `fund`), then:

```powershell
docker compose -f databases.yaml up -d
kubectl apply -f kubernetes/system.yaml
kubectl get pods
```

### Alternative: Docker Desktop's built-in Kubernetes

Instead of kind, you can use the Kubernetes that comes with Docker Desktop (Settings → Kubernetes → Enable Kubernetes). It uses the same image store as Docker, so there's no `kind load` step.

1. Start Docker Desktop and wait until it shows "Kubernetes running".
2. Pull and build the images:

   ```powershell
   docker compose pull authentication-database mongo redis
   $env:BUILDX_NO_DEFAULT_ATTESTATIONS="1"
   docker compose build
   ```

3. Check that the images are there: `docker images`
4. Apply the manifest:

   ```powershell
   kubectl apply -f kubernetes/system.yaml
   kubectl get pods
   ```

Wait until all pods are `Running`.

### After changing the code

Rebuild only the service you changed, load it into the cluster and restart it. Example for `director`:

```powershell
$env:BUILDX_NO_DEFAULT_ATTESTATIONS="1"
docker compose build director
kind load docker-image investment-fund-director:k8s --name fund
kubectl rollout restart deployment director-deployment
kubectl get pods
```

For the other services, replace `director` with `authentication` or `employee`. With Docker Desktop's Kubernetes, skip the `kind load` line.

## Trying it out

Default director account:

```
email:    onlymoney@gmail.com
password: evenmoremoney
```

Register an employee:

```
POST http://127.0.0.1:30000/register
{"forename": "Test", "surname": "Test", "email": "test@gmail.com", "password": "password123"}
```

Log in:

```
POST http://127.0.0.1:30000/login
{"email": "test@gmail.com", "password": "password123"}
```

Use the `accessToken` from the response as `Authorization: Bearer <token>` for the employee (`:30001`) or director (`:30002`) endpoints.

### API overview

| Service | Endpoint | Method | Description |
|---|---|---|---|
| authentication | `/register` | POST | register an employee |
| authentication | `/login` | POST | log in, returns `accessToken` |
| authentication | `/delete` | POST | delete your own account |
| employee | `/search` | POST | search assets |
| employee | `/create_buy_order` | POST | propose a purchase |
| employee | `/create_sell_order` | POST | propose a sale |
| director | `/pending_orders` | GET | list pending proposals |
| director | `/decision` | POST | start a vote on a proposal, returns the voting transactions |
| director | `/report` | GET | per-category statistics |

All endpoints except `/register` and `/login` require the `Authorization: Bearer <token>` header.

### Checking that data survives a restart

1. Register a user.
2. Delete the MySQL pod: `kubectl delete pod authentication-database`
3. Run `kubectl apply -f kubernetes/system.yaml` and wait for the new pod with `kubectl get pods`.
4. Log in with the same user. If you get a token, the data was kept on the PersistentVolume.

## Useful commands

**Logs and debugging**

```powershell
kubectl get pods
kubectl logs deployment/authentication-deployment
kubectl logs deployment/employee-deployment
kubectl logs -f deployment/director-deployment
kubectl describe pod <pod-name>
docker images | Select-String investment
```

**If Docker Desktop's Kubernetes won't start**

Check that kubectl sees the cluster and is using the right context:

```powershell
kubectl get nodes
kubectl config current-context
```

If it's stuck while starting, pulling the pause image manually and starting Kubernetes again from Docker Desktop can help:

```powershell
docker pull registry.k8s.io/pause:3.10
```

**Clearing data** (keeps the director account)

```powershell
kubectl exec -it authentication-database -- mysql -uroot -proot -e "DELETE FROM fund.users WHERE email != 'onlymoney@gmail.com';"
kubectl exec -it mongo -- mongosh -u root -p example --authenticationDatabase admin --eval "db.getSiblingDB('investment_fund').assets.deleteMany({})"
kubectl exec -it redis -- redis-cli FLUSHALL
```

**Removing everything, including volumes**

```powershell
kubectl delete -f kubernetes/system.yaml
kubectl delete pv authentication-database-volume mongo-volume
kubectl get pv
kubectl get pvc
```

If a volume stays in `Terminating` for more than a minute, remove its finalizers and run the two delete commands again:

```powershell
kubectl patch pvc authentication-database-claim --type=merge -p '{\"metadata\":{\"finalizers\":null}}'
kubectl patch pvc mongo-claim --type=merge -p '{\"metadata\":{\"finalizers\":null}}'
kubectl patch pv authentication-database-volume --type=merge -p '{\"metadata\":{\"finalizers\":null}}'
kubectl patch pv mongo-volume --type=merge -p '{\"metadata\":{\"finalizers\":null}}'
```

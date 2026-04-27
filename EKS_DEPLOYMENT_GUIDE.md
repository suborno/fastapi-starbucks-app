# Deploying Starbucks FastAPI to AWS EKS

This guide will walk you through the process of deploying your Starbucks FastAPI microservice from scratch onto an Amazon Elastic Kubernetes Service (EKS) cluster.

## Prerequisites

Before starting, ensure you have the following tools installed and configured on your machine:
1. **[AWS CLI](https://aws.amazon.com/cli/)**: Installed and configured with your AWS credentials (`aws configure`).
2. **[eksctl](https://eksctl.io/)**: The official CLI for Amazon EKS.
3. **[kubectl](https://kubernetes.io/docs/tasks/tools/)**: The Kubernetes command-line tool.
4. **[Docker](https://docs.docker.com/get-docker/)**: Running locally to build and push your container image.

---

## Step 1: Create the EKS Cluster

We will use `eksctl` to provision a managed Kubernetes cluster. This process creates the underlying VPC, security groups, and worker nodes.

Open your terminal and run the following command:

```bash
eksctl create cluster \
  --name starbucks-cluster \
  --region ap-south-2 \
  --nodegroup-name standard-workers \
  --node-type t3.small \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed
```

> [!WARNING]  
> **AWS Free Tier Limitations:** While `t3.small` EC2 instances are eligible for the AWS Free Tier, the **Amazon EKS Control Plane is NOT free**. EKS costs $0.10 per hour (approx. $73/month). If you absolutely need a 100% free Kubernetes environment, consider running a lightweight distribution like `k3s` or `minikube` directly on a single `t3.small` EC2 instance instead.
> 
> Furthermore, be sure to complete **Step 7 (Clean Up)** immediately after testing to stop incurring hourly charges.

> [!NOTE]  
> Cluster provisioning usually takes about **15 to 20 minutes**. Grab a coffee while AWS sets up the infrastructure!

Once the cluster is created, `eksctl` automatically updates your local `~/.kube/config` file, so `kubectl` is immediately ready to communicate with your new EKS cluster.

Test your connection:
```bash
kubectl get nodes
```

---

## Step 2: Set Up AWS Elastic Container Registry (ECR)

Kubernetes needs a place to pull your Docker image from. We'll use AWS ECR.

1. **Create an ECR Repository**:
   ```bash
   aws ecr create-repository \
     --repository-name starbucks-fastapi \
     --region ap-south-2
   ```
   *Take note of the `repositoryUri` output from this command (e.g., `123456789012.dkr.ecr.ap-south-2.amazonaws.com/starbucks-fastapi`).*

2. **Authenticate Docker to ECR**:
   ```bash
   aws ecr get-login-password --region ap-south-2 | docker login --username AWS --password-stdin 617029295065.dkr.ecr.ap-south-2.amazonaws.com
   ```

---

## Step 3: Build and Push Your Docker Image

1. **Build the image**:
   Ensure you are in the root directory of your project (where the `Dockerfile` is located).
   ```bash
   docker build -t starbucks-fastapi:latest .
   ```

2. **Tag the image for ECR**:
   ```bash
   docker tag starbucks-fastapi:latest 617029295065.dkr.ecr.ap-south-2.amazonaws.com/starbucks-fastapi:latest
   ```

3. **Push the image to ECR**:
   ```bash
   docker push 617029295065.dkr.ecr.ap-south-2.amazonaws.com/starbucks-fastapi:latest
   ```

---

## Step 4: Update Your Kubernetes Manifests

Before deploying, you must tell Kubernetes where to find your newly uploaded image.

1. Open `k8s/deployment.yaml`.
2. Locate the `image` line under `containers`.
3. Update it to point to your ECR URI:
   
```diff
    spec:
      containers:
      - name: starbucks-fastapi
-       image: starbucks-fastapi:latest
+       image: 617029295065.dkr.ecr.ap-south-2.amazonaws.com/starbucks-fastapi:latest
        ports:
```

---

## Step 5: Deploy the Application

Now deploy your manifests to the EKS cluster.

```bash
# Apply the deployment and service
kubectl apply -f k8s/
```

Verify that your pods are spinning up:
```bash
kubectl get pods -l app=starbucks-fastapi
```

---

## Step 6: Access Your Starbucks App

Your `service.yaml` defines a `LoadBalancer`, which tells AWS to provision a Classic Load Balancer to route external traffic to your pods.

Get the external URL assigned by AWS:
```bash
kubectl get service starbucks-fastapi-service
```

Look for the `EXTERNAL-IP` column. It will look something like `a1b2c3d4e5f6...ap-south-2.elb.amazonaws.com`.

> [!TIP]  
> It may take 2-3 minutes for the AWS Load Balancer to fully provision and register the targets. 

Once ready, open your browser and go to:
- **`http://<EXTERNAL-IP>/docs`** to see your interactive Swagger API menu.

---

## Step 7: Clean Up (Important!)

EKS clusters and Load Balancers incur hourly charges. When you are done testing, **do not forget to delete your resources** to avoid unexpected AWS bills.

1. **Delete the Kubernetes Service (removes the Load Balancer)**:
   ```bash
   kubectl delete service starbucks-fastapi-service
   ```

2. **Delete the EKS Cluster**:
   ```bash
   eksctl delete cluster --name starbucks-cluster --region ap-south-2
   ```

3. **Delete the ECR Repository** (Optional):
   ```bash
   aws ecr delete-repository --repository-name starbucks-fastapi --force --region ap-south-2
   ```

---

## Step 8: Automating Deployments with Jenkins CI/CD

Now that you've verified your cluster and application work manually, you can automate this using the provided `Jenkinsfile`.

### Prerequisites for Jenkins
1. A running Jenkins server (can be installed on an EC2 instance or locally).
2. The following Jenkins plugins installed: **Git**, **Docker Pipeline**, **Kubernetes CLI**, and **Credentials Binding**.
3. Jenkins needs Docker installed and permission to run `docker` commands (often by adding the `jenkins` user to the `docker` group).
4. Jenkins needs `kubectl` and `aws-cli` installed to interact with EKS.

### 1. Configure Jenkins Credentials
To allow Jenkins to push images to AWS ECR and deploy to EKS, you must securely store your credentials in Jenkins.

- **Kubernetes Kubeconfig**:
  1. Go to **Manage Jenkins** -> **Credentials** -> **System** -> **Global credentials** -> **Add Credentials**.
  2. Kind: **Secret file**.
  3. Upload your `~/.kube/config` file (which was generated by `eksctl` in Step 1).
  4. ID: `k8s-kubeconfig` (this matches the `Jenkinsfile`).

- **AWS Credentials (for ECR)**:
  For AWS ECR, it is highly recommended to configure the Jenkins server's AWS CLI with an IAM Role (if running on an EC2 instance) or configure the AWS credentials directly on the Jenkins host. The pipeline script uses the AWS CLI to authenticate.

### 2. Update the `Jenkinsfile`
Open your `Jenkinsfile` and ensure the environment variables match your AWS ECR setup:

```groovy
    environment {
        DOCKER_IMAGE = 'starbucks-fastapi'
        // Replace with your ECR URI
        DOCKER_REGISTRY = '617029295065.dkr.ecr.ap-south-2.amazonaws.com'
        IMAGE_TAG = "${env.BUILD_ID}"
        
        KUBECONFIG_ID = 'k8s-kubeconfig'
    }
```

*Because we are using AWS ECR*, you will need to modify the "Push Docker Image" stage in the `Jenkinsfile` to use the AWS CLI for login instead of the default `withCredentials` block:

```diff
        stage('Push Docker Image') {
            steps {
                script {
-                   echo "Pushing Docker Image to Registry"
-                   withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDS_ID}", passwordVariable: 'DOCKER_PASSWORD', usernameVariable: 'DOCKER_USERNAME')]) {
-                       sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin"
+                   echo "Pushing Docker Image to AWS ECR"
+                   // AWS CLI login
+                   sh "aws ecr get-login-password --region ap-south-2 | docker login --username AWS --password-stdin ${DOCKER_REGISTRY}"
                        sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${IMAGE_TAG}"
                        sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest"
-                   }
                }
            }
        }
```

### 3. Create the Jenkins Pipeline Job
1. In the Jenkins dashboard, click **New Item**.
2. Enter a name (e.g., `Starbucks-FastAPI-Deployment`) and select **Pipeline**, then click OK.
3. Under the **Pipeline** section, choose **Pipeline script from SCM**.
4. SCM: **Git**.
5. Provide your repository URL (push this code to a Git repository like GitHub or Bitbucket first).
6. Script Path: `Jenkinsfile`.
7. Click **Save**.

### 4. Run the Pipeline
Click **Build Now**. Jenkins will:
1. Pull the latest code.
2. Build the Docker image.
3. Push it to your AWS ECR.
4. Update your EKS cluster with the new image tag.

You now have a fully automated CI/CD pipeline!

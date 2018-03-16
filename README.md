# Easy Kubernetes Cluster on Ubuntu 16.04 Using Kubespray (Formerly Kargo) v2.2.0.

## Requirements
1. Three Ubuntu 16.04 VMs or Bare Metal installs with **no swap**.  I used Parallels VMs with 4G RAM and 4 Cores each.
    * The following packages should be installed:
        * python
        * python-minimal
        * openssh-server
    * All three should have the same user with password-free sudo access.  In this guide, my username is **ubuntu**.
    * Each of the three should have unfiltered network access to the other two.
    * You should have a private ssh key which gives you access to the aforementioned user.
1. A local docker install with the aronahl/kargo image.

## Steps
1. Configure the inventory of your three machines.  Assuming the IP addresses of your three machines are 10.0.0.1, 10.0.0.2, and 10.0.0.3:

    ```bash
    $ docker run --rm -it -v kube-data:/usr/local/share/kubespray aronahl/kargo python3 ./contrib/inventory_builder/inventory.py 10.0.0.1 10.0.0.2 10.0.0.3
    ```
    
    This will create a kube-data docker volume populated with Kargo's ansible files and your new inventory config file.  Be careful to avoid having an existing config in the volume, or you will end up running the buildout against hosts that you don't intent to change (or that may not exist).
    
1. Copy your ssh private key to the kube-data volume.  In my case, the file is called **kube_ecdsa**.

    ```bash
    $ docker run --rm -i -v kube-data:/data busybox tee /data/id_ecdsa < kube_ecdsa
    $ docker run --rm -v kube-data:/data busybox chmod 600 /data/id_ecdsa
    ```
    
1. Configure the cluster.

    ```bash
    $ docker run --rm -it -v kube-data:/usr/local/share/kubespray aronahl/kargo \
      ansible-playbook -i ./inventory.cfg cluster.yml -b -v --private-key=./id_ecdsa \
      -u ubuntu -e kube_version=v1.9.2 -e kube_api_pwd=mysup3rs3cr3tp455w0rd
    ```
    
1. Download the config for your local kubectl

	```bash
	$ ssh -i kube_ecdsa ubuntu@10.0.0.1 sudo cat /etc/kubernetes/admin.conf > ~/.kube/config
	```
1. Use it.

    ```bash
	$ kubectl --namespace=kube-system get pods
	NAME                                    READY     STATUS    RESTARTS   AGE
	calico-node-894bv                       1/1       Running   0          20m
	calico-node-gxws8                       1/1       Running   0          20m
	calico-node-w6sxv                       1/1       Running   0          20m
	kube-apiserver-node1                    1/1       Running   0          19m
	kube-apiserver-node2                    1/1       Running   0          19m
	kube-controller-manager-node1           1/1       Running   0          20m
	kube-controller-manager-node2           1/1       Running   0          20m
	kube-dns-79d99cdcd5-ggh9c               3/3       Running   0          19m
	kube-dns-79d99cdcd5-w6tlb               3/3       Running   0          19m
	kube-proxy-node1                        1/1       Running   0          19m
	kube-proxy-node2                        1/1       Running   0          19m
	kube-proxy-node3                        1/1       Running   0          19m
	kube-scheduler-node1                    1/1       Running   0          20m
	kube-scheduler-node2                    1/1       Running   0          20m
	kubedns-autoscaler-5564b5585f-fjcnt     1/1       Running   0          19m
	kubernetes-dashboard-6bbb86ffc4-5bdr6   1/1       Running   0          19m
	nginx-proxy-node3                       1/1       Running   0          19m
    ```
1. Check out the UI

	```bash
	$ kubectl proxy
	```
	Visit [http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/login](http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/login) and select _skip_.

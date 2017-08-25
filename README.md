# Easy Kubernetes Cluster on Ubuntu 16.04 Using Kubespray (Formerly Kargo) v2.1.2.

## Requirements
1. Three Ubuntu 16.04 VMs or Bare Metal installs.  I used Parallels VMs with 4G RAM and 4 Cores each.
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
    $ docker run --rm -it -v kube-data:/usr/local/share/kargo aronahl/kargo python3 ./contrib/inventory_builder/inventory.py 10.0.0.1 10.0.0.2 10.0.0.3
    ```
    
    This will create a kube-data docker volume populated with Kargo's ansible files and your new inventory config file.  Be careful to avoid having an existing config in the volume, or you will end up running the buildout against hosts that you don't intent to change (or that may not exist).
    
1. Copy your ssh private key to the kube-data volume.  In my case, the file is called **kube_ecdsa**.

    ```bash
    $ docker run --rm -i -v kube-data:/data busybox tee /data/id_ecdsa < kube_ecdsa
    $ docker run --rm -v kube-data:/data busybox chmod 600 /data/id_ecdsa
    ```
    
1. Configure the cluster.

    ```bash
    $ docker run --rm -it -v kube-data:/usr/local/share/kargo aronahl/kargo ansible-playbook -i ./inventory.cfg cluster.yml -b -v --private-key=./id_ecdsa -u ubuntu -e kube_version=v1.6.7
    ```
    If it fails or locks up, run it a second time (yuck).
    
1. Set up your local kubectl client in ~/.kube/config

    **Caution:** This is insecure, hence the term *insecure*.

    ```yaml
    apiVersion: v1
    clusters:
    - cluster:
        server: https://10.0.0.1:6443
        insecure-skip-tls-verify: true
      name: clusty
    contexts:
    - context:
        cluster: clusty
        user: kube
      name: clustycon
    current-context: clustycon
    kind: Config
    preferences: {}
    users:
    - name: kube
      user:
        password: changeme
        username: kube
    ```
1. Use it.

    ```bash
	$ kubectl --namespace=kube-system get pods
	NAME                                  READY     STATUS    RESTARTS   AGE
	dnsmasq-1375889904-njj7p              1/1       Running   0          2m
	dnsmasq-autoscaler-3605072793-x5q1l   1/1       Running   0          2m
	kube-apiserver-kube001                1/1       Running   0          2m
	kube-apiserver-kube002                1/1       Running   0          2m
	kube-controller-manager-kube001       1/1       Running   0          2m
	kube-controller-manager-kube002       1/1       Running   0          2m
	kube-proxy-kube001                    1/1       Running   0          2m
	kube-proxy-kube002                    1/1       Running   0          1m
	kube-proxy-kube003                    1/1       Running   0          1m
	kube-scheduler-kube001                1/1       Running   0          2m
	kube-scheduler-kube002                1/1       Running   0          2m
	kubedns-1519522227-bm956              3/3       Running   0          2m
	kubedns-autoscaler-1428750645-6nbhq   1/1       Running   0          2m
	nginx-proxy-kube003                   1/1       Running   0          2m
    ```

1. Maybe install the UI.

    ```bash
    $ kubectl create -f https://raw.githubusercontent.com/kubernetes/dashboard/v1.6.3/src/deploy/kubernetes-dashboard.yaml
    $ kubectl expose service --name kubernetes-dashboard-external --namespace=kube-system kubernetes-dashboard --external-ip=10.0.0.1 --port=9090
    ```
    
    Browse to http://10.0.0.1:9090/

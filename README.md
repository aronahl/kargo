# Easy Kubernetes Cluster on Ubuntu 16.04 Using Kargo v2.1.1.

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
	
	This will create a kube-data docker volume populated with Kargo's ansible files and your new inventory config file.
	
1. Copy your ssh private key to the kube-data volume.  In my case, the file is called **kube_rsa**.

	```bash
	$ docker run --rm -i -v kube-data:/data busybox tee /data/id_rsa < kube_rsa
	$ docker run --rm -v kube-data:/data busybox chmod 600 /data/id_rsa
	```
	
1. Configure the cluster.

	```bash
	$ docker run --rm -it -v kube-data:/usr/local/share/kargo aronahl/kargo ansible-playbook -i ./inventory.cfg cluster.yml -b -v --private-key=./id_rsa -u ubuntu -e deploy_netchecker=true
	```
	If it fails, run it a second time (yuck).
	
1. Validate networking
	* SSH to the master node and run

	```bash
	curl http://localhost:31081/api/v1/connectivity_check
	```
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
	$ kubectl get pods
	NAME                             READY     STATUS    RESTARTS   AGE
	netchecker-agent-d7fj3           1/1       Running   0          1h
	netchecker-agent-hostnet-mf3hh   1/1       Running   0          1h
	netchecker-agent-hostnet-v0f1h   1/1       Running   0          1h
	netchecker-agent-hostnet-vs4nj   1/1       Running   0          1h
	netchecker-agent-sdr64           1/1       Running   0          1h
	netchecker-agent-z1zgm           1/1       Running   0          1h
	netchecker-server                1/1       Running   0          1h
	```

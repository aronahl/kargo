#!/usr/local/bin/python3.6 -u
import subprocess
import re
from ipaddress import IPv4Address
import time
from textwrap import dedent
import os.path

if __name__ == "__main__":
    kubes = ("Kube001", "Kube002", "Kube003")
    kube_addresses = []
    for kube in kubes:
        subprocess.check_call(args=("prlctl", "stop", kube, "--kill"))
        subprocess.check_call(args=("prlctl", "delete", kube))

        subprocess.check_call(args=("prlctl", "clone", "KubeBase", "--name", kube, "--linked"))
        subprocess.check_call(args=("prlctl", "start", kube))
        while subprocess.Popen(args=("prlctl", "exec", kube, "uptime")).wait() != 0:
            time.sleep(1)
        for address in [IPv4Address(x[-1]) for x in re.findall("(\s+inet addr:)([0-9.]+)", subprocess.check_output(args=("prlctl", "exec", kube, "ifconfig")).decode("utf-8"))]:
            if not address.is_loopback:
                kube_addresses.append(address.exploded)
    assert len(kubes) == len(kube_addresses)
    subprocess.check_call(args=("docker", "volume", "rm", "kube-data", "--force"))
    subprocess.check_call(args=["docker", "run", "--rm", "-i", "-v", "kube-data:/usr/local/share/kubespray", "aronahl/kargo", "python3", "./contrib/inventory_builder/inventory.py"] + kube_addresses)
    with open("kube_ecdsa") as f:
        subprocess.check_call(args=("docker", "run", "--rm", "-i", "-v", "kube-data:/data", "busybox", "tee", "/data/id_ecdsa"), stdin = f)
        subprocess.check_call(args=("docker", "run", "--rm", "-v", "kube-data:/data", "busybox", "chmod", "600", "/data/id_ecdsa"))
    subprocess.check_call(args=("docker", "run", "--name", "kuber-gooding", "-it", "--rm", "-v", "kube-data:/usr/local/share/kubespray", "aronahl/kargo", "ansible-playbook", "-i", "./inventory.cfg", "cluster.yml", "-b", "-v", "--private-key=./id_ecdsa", "-u", "ubuntu", "-e", "kube_version=v1.7.3", "-e", "kube_api_pwd=mysup3rs3cr3tp455w0rd"))
    with open(os.path.expanduser("~/.kube/config"), "w") as f:
        f.write(dedent('''\
            apiVersion: v1
            clusters:
            - cluster:
                server: https://%s:6443
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
                password: mysup3rs3cr3tp455w0rd
                username: kube
                ''' % kube_addresses[0]))
    subprocess.check_call(args=("kubectl", "run", "ca", "--image=busybox", "--restart=Never", "--command", "cat", "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"))
    time.sleep(5)
    with open(os.path.expanduser("~/.kube/clusty.ca"), "w") as f:
        subprocess.check_call(args=("kubectl", "logs", "ca"), stdout = f)
    subprocess.check_call(args=("kubectl", "delete", "pod", "ca"))
    with open(os.path.expanduser("~/.kube/config"), "w") as f:
        f.write(dedent('''\
            apiVersion: v1
            clusters:
            - cluster:
                server: https://%s:6443
                certificate-authority: clusty.ca
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
                password: mysup3rs3cr3tp455w0rd
                username: kube
                ''' % kube_addresses[0]))
    subprocess.check_call(args=("kubectl", "--namespace=kube-system", "get", "pods"))
    subprocess.check_call(args=("kubectl", "create", "-f", "https://raw.githubusercontent.com/kubernetes/dashboard/v1.6.3/src/deploy/kubernetes-dashboard.yaml"))
    subprocess.check_call(args=("kubectl", "expose", "service", "--name", "kubernetes-dashboard-external", "--namespace=kube-system", "kubernetes-dashboard", "--external-ip=%s" % kube_addresses[0], "--port=9090"))

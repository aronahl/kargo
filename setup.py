#!/usr/local/bin/python3.6 -u
'''
I use this script to deploy a 3-member cluster using parallels desktop pro.

I already have a template VM called KubeBase with access for user ubuntu via a key called kube_ecdsa.
'''
import os.path
import re
import subprocess
import time
from ipaddress import IPv4Address
from textwrap import dedent


def banner_message(msg):
    mid = "##  %s  ##" % msg
    tb = '#' * len(mid)
    print("\n".join((tb, mid, tb)))


def stop_vm(vm_name):
    banner_message("Stopping %s" % vm_name)
    subprocess.Popen(args=("prlctl", "stop", vm_name, "--kill")).wait()


def delete_vm(vm_name):
    banner_message("Deleting %s" % vm_name)
    subprocess.Popen(args=("prlctl", "delete", vm_name)).wait()


def create_vm(vm_name):
    banner_message("Creating %s" % vm_name)
    subprocess.check_call(args=("prlctl", "clone", "KubeBase", "--name", vm_name, "--linked"))
    subprocess.check_call(args=("prlctl", "start", vm_name))
    with open("/dev/null") as f:
        while subprocess.Popen(args=("prlctl", "exec", vm_name, "uptime"), stdout=f, stderr=f).wait() != 0:
            time.sleep(1)


def get_vm_address(vm_name):
    banner_message("Getting address of %s" % vm_name)
    for address in [IPv4Address(x[-1]) for x in re.findall("(\s+inet addr:)([0-9.]+)", subprocess.check_output(
            args=("prlctl", "exec", vm_name, "ifconfig")).decode("utf-8"))]:
        if not address.is_loopback:
            return address.exploded


def create_inventory(kube_addresses):
    banner_message("Creating Inventory")
    subprocess.check_call(args=("docker", "volume", "rm", "kube-data", "--force"))
    subprocess.check_call(
        args=["docker", "run", "--rm", "-it", "-v", "kube-data:/usr/local/share/kubespray", "aronahl/kargo", "python3",
              "./contrib/inventory_builder/inventory.py"] + kube_addresses)


def upload_key():
    banner_message("Uploading key")
    with open("kube_ecdsa") as f:
        subprocess.check_call(
            args=("docker", "run", "--rm", "-i", "-v", "kube-data:/data", "busybox", "tee", "/data/id_ecdsa"), stdin=f)
        subprocess.check_call(
            args=("docker", "run", "--rm", "-v", "kube-data:/data", "busybox", "chmod", "600", "/data/id_ecdsa"))


def run_ansible():
    banner_message("Running Ansible")
    subprocess.check_call(args=(
        "docker", "run", "--name", "kuber-gooding", "-it", "--rm", "-v", "kube-data:/usr/local/share/kubespray",
        "aronahl/kargo", "ansible-playbook", "-i", "./inventory.cfg", "cluster.yml", "-b", "-v",
        "--private-key=./id_ecdsa",
        "-u", "ubuntu", "-e", "kube_version=v1.7.3", "-e", "kube_api_pwd=mysup3rs3cr3tp455w0rd"))


def write_insecure_config(address):
    banner_message("Writing Insecure Config")
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
                ''' % address))


def download_cert():
    banner_message("Downloading Cert")
    subprocess.check_call(args=("kubectl", "run", "ca", "--image=busybox", "--restart=Never", "--command", "cat",
                                "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"))
    time.sleep(5)
    with open(os.path.expanduser("~/.kube/clusty.ca"), "w") as f:
        subprocess.check_call(args=("kubectl", "logs", "ca"), stdout=f)
    subprocess.check_call(args=("kubectl", "delete", "pod", "ca"))


def write_secure_config(address):
    banner_message("Writing Secure Config")
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
                ''' % address))


def write_configs(address):
    write_insecure_config(address)
    download_cert()
    write_secure_config(address)


def ping_kube():
    banner_message("Pinging Kube")
    subprocess.check_call(args=("kubectl", "--namespace=kube-system", "get", "pods"))


def install_dashboard(address):
    banner_message("Installing Dashboard at %s" % address)
    subprocess.check_call(args=("kubectl", "create", "-f",
                                "https://raw.githubusercontent.com/kubernetes/dashboard/v1.6.3/"
                                "src/deploy/kubernetes-dashboard.yaml"))
    subprocess.check_call(args=(
        "kubectl", "expose", "service", "--name", "kubernetes-dashboard-external", "--namespace=kube-system",
        "kubernetes-dashboard", "--external-ip=%s" % address, "--port=9090"))


def main():
    kubes = ("Kube001", "Kube002", "Kube003")
    kube_addresses = []
    for kube in kubes:
        stop_vm(kube)
        delete_vm(kube)
        create_vm(kube)
        kube_addresses.append(get_vm_address(kube))

    assert len(kubes) == len(kube_addresses)

    create_inventory(kube_addresses)
    upload_key()
    run_ansible()
    write_configs(kube_addresses[0])
    ping_kube()
    install_dashboard(kube_addresses[0])
    banner_message("Dashboard: http://%s:9090" % kube_addresses[0])


if __name__ == "__main__":
    main()

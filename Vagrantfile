# -*- mode: ruby -*-
# vi: set ft=ruby :
#
$script = <<SCRIPT
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get upgrade -fyq
apt-get install -fyq python{,-minimal} openssh-server
cat >> /home/vagrant/.ssh/authorized_keys<<EOF
YOURPUBKEYHERE
EOF
sed -e 's/.*swap.*//g' -i /etc/fstab
swapoff -a
SCRIPT

Vagrant.configure("2") do |config|
    config.vm.provision "shell", inline: $script
    config.vm.define "one" do |one|
        one.vm.box = "bento/ubuntu-16.04"
        one.vm.provider "parallels" do |pl|
            pl.memory = "4096"
            pl.cpus = 4
        end
    end
    config.vm.define "two" do |two|
        two.vm.box = "bento/ubuntu-16.04"
        two.vm.provider "parallels" do |pl|
            pl.memory = "4096"
            pl.cpus = 4
        end
    end
    config.vm.define "three" do |three|
        three.vm.box = "bento/ubuntu-16.04"
        three.vm.provider "parallels" do |pl|
            pl.memory = "4096"
            pl.cpus = 4
        end
    end
end

# -*- mode: ruby -*-
# vi: set ft=ruby :

require "json"
require "time"

devconfig = JSON.parse(File.read("config/devconfig.json"))

def setup_host
  if !(`netstat -nr`.include? "198.38.24/21")
    puts "Adding routes to host computer..."
    if `uname -s`.chomp == "Darwin"
      cmd = "sudo route add 198.38.24.0/21 198.38.22.126"
    else
      cmd = "sudo route add -net 198.38.24.0 gw 198.38.22.126 netmask 255.255.248.0"
    end
    puts cmd
    exit if !system(cmd)
  end
end

# Make sure the host computer is set up every time a vagrant command is run
setup_host


VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.network "public_network"
  config.vm.network "forwarded_port", guest: 8080, host: 8080

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
    vb.customize ["modifyvm", :id, "--nictype1", "virtio"]
  end

  config.vm.synced_folder ".", "/vagrant", disabled: true
  config.vm.synced_folder ".", "/home/vagrant/intranet"

  config.vm.provision "file",
    source: "~/.ssh/#{devconfig['ssh_key']}",
    destination: ".ssh/#{devconfig['ssh_key']}"

  config.vm.provision "file",
    source: "~/.ssh/#{devconfig['ssh_key']}.pub",
    destination: ".ssh/#{devconfig['ssh_key']}.pub"

  config.vm.provision "shell", path: "config/provision_vagrant.sh"
end

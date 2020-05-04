# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 2.2.7"

require "json"
require "time"

devconfig = JSON.parse(File.read("config/devconfig.json"))

def setup_host
  return unless ["up", "resume", "ssh", "reload"].include? ARGV[0]

  if !(`netstat -nr`.include? "198.38.")
    puts "Adding routes to host computer..."
    if RUBY_PLATFORM =~ /darwin/
      cmd = "sudo route add 198.38.24.0/21 198.38.22.126"
    elsif RUBY_PLATFORM =~ /mingw/
     cmd = "route add 198.38.24.0 mask 255.255.248.0 198.38.22.126"
    else
      cmd = "sudo route add -net 198.38.24.0 gw 198.38.22.126 netmask 255.255.248.0"
    end
    puts cmd
    exit if !system(cmd)
    if RUBY_PLATFORM =~ /mingw/
     pingcmd = "ping -n 1 198.38.27.6"
    else
     pingcmd = "ping -c1 198.38.27.6"
    end
    if !system(pingcmd)
      puts "Can not reach KDC for LOCAL.TJHSST.EDU realm. Try toggling VPN and deleting and re-adding the route."
      exit
    end
  end
end

# Make sure the host computer is set up every time a vagrant command is run
if devconfig["use_vpn"]
    setup_host
end


Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.vm.boot_timeout = 1000
  if devconfig["use_vpn"]
      config.vm.network "public_network", bridge: devconfig["network_interface"]
  end
  config.vm.network "forwarded_port", guest: 8080, host: 8080
  config.vm.network "forwarded_port", guest: 5555, host: 5555

  config.ssh.forward_agent = true

  config.vm.hostname = "ionvm"

  config.vm.define "ion-vagrant" do |v|
  end

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
    vb.customize ["modifyvm", :id, "--nictype1", "virtio"]
    vb.name = "ion-vagrant"
    vb.memory = 2048 # the default of 512 gives us a OOM during setup.
    # vb.gui = true
  end



  config.vm.network :private_network, ip: '192.168.50.50'
  if devconfig["use_nfs"]
      config.vm.synced_folder ".", "/home/vagrant/intranet", type: :nfs, nfs_udp: false
      config.nfs.map_uid = Process.uid
      config.nfs.map_gid = Process.gid
  else
      config.vm.synced_folder ".", "/home/vagrant/intranet"
  end

  config.vm.provision "file",
    source: "~/.ssh/#{devconfig['ssh_key']}",
    destination: ".ssh/#{devconfig['ssh_key']}"

  config.vm.provision "file",
    source: "~/.ssh/#{devconfig['ssh_key']}.pub",
    destination: ".ssh/#{devconfig['ssh_key']}.pub"

  config.vm.provision "shell", path: "config/provision_vagrant.sh"

  config.ssh.username = "vagrant"
end

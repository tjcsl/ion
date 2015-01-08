# -*- mode: ruby -*-
# vi: set ft=ruby :

def setup_host
  if !(`route get 198.38.16.92`.include? "ion.tjhsst.edu") # pick better one
    puts "You must be connected to VPN."
    exit 1
  end

  if !(`netstat -nr`.include? "198.38.24/21")
    if `uname -s`.chomp == "Darwin"
      exit if !system("sudo route add 198.38.24.0/21 198.38.22.126")
    else
      exit if !system("sudo route add 198.38.24.0/21 gw 198.38.22.126")
    end
  end
end

# Make sure the host computer is set up every time a vagrant command is run
setup_host


VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/trusty64"
  config.vm.provision "shell", path: "provision.sh"
  config.vm.provision "file", source: "~/.gitconfig", destination: ".gitconfig"
end

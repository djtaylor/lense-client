# Lense Client Libraries

Client libraries for interacting with the Lense platform.

### Repository

To make the Lense packages available, you will need to add the following PPA and import the signing key:

```sh
$ sudo add-apt-repository ppa:djtaylor13/main
$ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys DAA6AF94
$ sudo apt-get update
```

### Installation

You can install 'lense-client' and its requirements with the following commands:

```sh
$ sudo apt-get install lense-client
$ sudo pip install -r /usr/share/doc/lense/requirements.client.txt
```
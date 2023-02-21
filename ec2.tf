terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.54.0"
    }
  }
}

provider "aws" {
  region     = var.region
  # Hard-coding credentials is not recommended
  access_key = var.access_key
  secret_key = var.secret_key
}

resource "aws_instance" "example" {
  ami = "ami-0454bb2fefc7de534"
  instance_type = "t2.micro"

  tags = {
    Name = "trial-instance2"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get install -y python3-pip",
      "pip3 install -r requirements.txt",
      "python3 bot.py",
    ]
  }
}



output "ec2_ip" {
    value = aws_instance.ec2.private_ip
}
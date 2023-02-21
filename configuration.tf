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

resource "aws_instance" "ec2" {
  ami = "ami-0a5a6128e65676ebb"
  instance_type = "t2.micro"

  tags = {
    Name = "trial-instance"
  }
}
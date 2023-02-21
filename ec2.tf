provider "aws" {
  
}

resource "aws_instance" "ec2" {
  ami = "ami-0454bb2fefc7de534"
  instance_type = "t2.micro"
}

output "ec2_ip" {
    value = aws_instance.ec2.private_ip
}
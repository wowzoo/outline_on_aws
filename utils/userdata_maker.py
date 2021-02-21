import boto3
import secrets
import os

from aws_cdk import aws_ec2 as ec2


class UserdataMaker(object):
    def __init__(self, db_url: str, redis_url: str, bucket_name: str):
        region = os.environ["CDK_REGION"]
        domain_name = os.environ["DOMAIN_NAME"]
        slack_key = os.environ["SLACK_KEY"]
        slack_secret = os.environ["SLACK_SECRET"]
        profile_name = os.environ["AWS_PROFILE"]
        smtp_host = os.environ["SMTP_HOST"]
        smtp_port = os.environ["SMTP_PORT"]
        smtp_username = os.environ["SMTP_USERNAME"]
        smtp_password = os.environ["SMTP_PASSWORD"]
        smtp_from = os.environ["SMTP_FROM_EMAIL"]
        smtp_reply = os.environ["SMTP_REPLY_EMAIL"]

        credentials = boto3.Session(profile_name=profile_name).get_credentials()

        self._data = ec2.UserData.for_linux()
        self._data.add_commands("sudo curl -sL https://rpm.nodesource.com/setup_14.x | sudo bash -")
        self._data.add_commands("sudo yum install -y nodejs")
        self._data.add_commands("sudo curl -sL https://dl.yarnpkg.com/rpm/yarn.repo | sudo tee /etc/yum.repos.d/yarn.repo")
        self._data.add_commands("sudo yum install -y yarn")
        self._data.add_commands("sudo amazon-linux-extras install -y docker")
        self._data.add_commands("sudo amazon-linux-extras install -y nginx1")

        # nginx
        self._data.add_commands("sudo rm /etc/nginx/nginx.conf")

        with open("resources/nginx/nginx.conf") as f:
            nginx_conf_data = f.read()
            self._data.add_commands(f"sudo echo '{nginx_conf_data}' > /etc/nginx/nginx.conf")

        with open("resources/nginx/outline.conf") as f:
            outline_conf_data = f.read()
            self._data.add_commands(f"sudo echo '{outline_conf_data}' > /etc/nginx/conf.d/outline.conf")
            self._data.add_commands(f"sudo sed -i 's=$outline_domain=outline.{domain_name}=' /etc/nginx/conf.d/outline.conf")

        self._data.add_commands("sudo systemctl start nginx")

        # outline config
        with open("resources/env.outline") as f:
            target_file_path = "/home/ec2-user/env.outline"
            outline_env_data = f.read()
            self._data.add_commands(f"sudo echo '{outline_env_data}' > {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$secret_key={secrets.token_hex(32)}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$utils_secret={secrets.token_hex(32)}=' {target_file_path}")
            # db/redis
            self._data.add_commands(f"sudo sed -i 's=$db_url={db_url}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$redis_url={redis_url}=' {target_file_path}")
            # domain url
            self._data.add_commands(f"sudo sed -i 's=$outline_domain=outline.{domain_name}=' {target_file_path}")
            # slack
            self._data.add_commands(f"sudo sed -i 's=$slack_key={slack_key}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$slack_secret={slack_secret}=' {target_file_path}")
            # s3 bucket
            self._data.add_commands(f"sudo sed -i 's=$aws_region={region}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$s3_bucket_name={bucket_name}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$s3_bucket_url=s3.{region}.amazonaws.com=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$aws_access_key={credentials.access_key}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$aws_secret_key={credentials.secret_key}=' {target_file_path}")
            # smtp
            self._data.add_commands(f"sudo sed -i 's=$smtp_host={smtp_host}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$smtp_port={smtp_port}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$smtp_username={smtp_username}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$smtp_password={smtp_password}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$smtp_from={smtp_from}=' {target_file_path}")
            self._data.add_commands(f"sudo sed -i 's=$smtp_reply={smtp_reply}=' {target_file_path}")

        # docker
        docker_image_name = "outlinewiki/outline"
        self._data.add_commands("sudo systemctl start docker")
        self._data.add_commands("sudo usermod -aG docker ec2-user")
        self._data.add_commands(f"sudo docker pull {docker_image_name}")
        self._data.add_commands(f"sudo docker run --rm --env-file={target_file_path} {docker_image_name} yarn sequelize:migrate")
        self._data.add_commands(f"sudo docker run -p 3000:3000 --env-file={target_file_path} -d {docker_image_name}")

        # ssh locale error fix
        self._data.add_commands("echo LANG=en_US.utf-8 | sudo tee /etc/environment")
        self._data.add_commands("echo LC_ALL=en_US.utf-8 | sudo tee -a /etc/environment")

    @property
    def data(self):
        return self._data

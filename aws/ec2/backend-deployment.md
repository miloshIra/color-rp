# Backend deployment

1. Create a new EC2 instance
    - name: `color-rp`
    - operating system: Ubuntu 24.04
    - instance type: `t2.micro`
    - create a new keypair `color-rp` and save the private key (contained in the `.pem` file) locally, and in AWS Secrets Manager
    - create a new security group `color-rp` and create new inboud and outbound rules with `0.0.0.0/0`

2. Setup an elastic IP address

3. Set up the EC2 instance
    - attach the elastic IP to the instance
    -  `ssh -i ~/.ssh/color-rp.pem ubuntu@art.coloring-ai.art`
    - [Generate a new SSH keypair][2] and copy the public key to [color-rp GitHub repo's][3] `Deployment keys` section under settings
    - set up the repo
        ```
        git clone https://github.com/miloshIra/color-rp
        cd color-rp
        bash ./aws/ec2/startup-script.sh
        touch .env
        nano .env
        ```
        - paste the content from [color-rp/.env][4] and save the file
    - create a systemd service
        ```
        sudo cp /home/ubuntu/color-rp/aws/ec2/color-rp.service /etc/systemd/system/color-rp.service
        sudo systemctl daemon-reload
        sudo systemctl enable color-rp.service
        sudo systemctl start color-rp.service
        sudo systemctl status color-rp.service
        ```
    - set up nginx
        ```
        sudo ln -s /home/ubuntu/color-rp/aws/ec2/color-rp.nginx /etc/nginx/sites-enabled/
        sudo systemctl restart nginx
        sudo systemctl enable nginx
        ```
    - set up SSL certificate
        ```
        sudo certbot --nginx -d api.coloring-ai.art
        sudo nginx -t
        sudo certbot renew --dry-run
        sudo systemctl restart nginx
        ```

4. You should now be able to access the service's endpoints via the public URL of the EC2 instance

5. Link the domain with the EC2 instance
    - create a new public hosted zone in Route 53
    - copy the NS record values to the NameCheap account under `Custom DNS`
    - create a new A-type record for `api.coloring-ai.art` and link it to the elastic IP

5. Redeployment

    - Manual via SSH

    ```
    ssh -i ~/.ssh/color-rp.pem ubuntu@art.coloring-ai.art

    cd /home/ubuntu/color-rp
    git pull
    # update the .env file if needed
    sudo systemctl restart color-rp.service
    sudo systemctl status color-rp.service
    ```

    - Manual via GitHub Workflows

        Manually trigger the `Deploy` workflow via GitHub Actions.

[1]: https://eu-central-1.console.aws.amazon.com/secretsmanager/secret?name=color-rp%2Fcolor-rp-ec2-private-key&region=eu-central-1
[2]: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent
[3]: https://github.com/miloshIra/color-rp
[4]: https://eu-central-1.console.aws.amazon.com/secretsmanager/secret?name=color-rp%2F.env&region=eu-central-1

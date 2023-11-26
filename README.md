# ETA-Watch Bot

A telegram bot which can access the current configuration of a ETA heating system.
Its abilities are:

* Retrieve the current config and save it as reference state
* Compare the current system config with the saved reference
* Update the reference state with the current state
* Edit the saved state (exclude config entries from diff)
* Resets everything to the whole config again

## Deployment

For easy deployment of this python project, a service file for systemd is given in the `deploy` folder.

Adjust the placeholder in the `eta-watch.service` file according to your environment and
copy the service file to the systemd directory for user services.
Typically, this is `/etc/systemd/system`, but it may vary depending on your Linux distribution.

Then execute the following commands to make it run as background service:

```bash
systemctl daemon-reload
# Start the service
systemctl start eta-watch.service
# Enable the service to run on boot
systemctl enable eta-watch.service
```

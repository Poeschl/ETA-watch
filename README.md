# ETA-Watch Bot

A telegram bot which can access the current configuration of a ETA heating system.
Its abilities are:

* Retrieve the current config and save it as reference state
* Checks on daily basis if the current state differs from the saved reference
* Edit the saved state (exclude config entries from diff)

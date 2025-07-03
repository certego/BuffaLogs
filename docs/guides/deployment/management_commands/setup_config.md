# Django Management Command: `setup_config`

## Description

The `setup_config` management command allows administrators or developers to programmatically set, add, or remove values from the customizable fields in the `Config` model, which acts as a centralized configuration store in the project.

This command supports different modes to control how values are written or modified.

## Usage

Run the command from the root of your Django project:

```bash
./manage.py setup_config [option] [FIELD=VALUE]
```
where `FIELD` is the name of one of the Config fields
and `option` is one of the following:

| Option | Name       | Description                                                                 |
|--------|------------|-----------------------------------------------------------------------------|
| `-o`   | Override   | Overwrites the VALUE for a given existing Config FIELD.                     |
| `-a`   | Append     | Append the VALUE to the FIELD [only for list fields]                        |
| `-r`   | Remove     | Removes the given VALUE from the targeted Config field.                     |


## Examples

### Override one or more Config field value

```bash
./manage.py setup_config -o enabled_users=["Lorygold","Lory"] -o alert_is_vip_only=True -o vel_accepted=500
```

### Append one or more Config field value (only for list fields)

```bash
./manage.py setup_config -a ignored_users=["bot", "BOT"] -a risk_score_increment_alerts=["Anonymous IP Login"]
```
### Remove one or more value from a Config field (only for list fields)
 
```bash
./manage.py setup_config -r ignored_users=["bot"] -r allowed_countries=["Italy", "Germany", "France"]
```

**The options could be mixed in a single command, but each FIELD=VALU pair must be preceded by the relevant option (-o / -a / -r).**


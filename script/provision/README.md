This folder contains a series of scripts to do the parts of provisioning that do not have UIs.

## Initial Provisioning

You need to start by copying sample.json in this directory and filling in your real values. The instructions for what the fill in for these values can be found in the provisioning guide, please reach out to a member of CCPO to access that document.

Once you've set up ATAT as prescribed in the root [README](../../README.md) and have populated the file with correct values, you can run each script in turn. The general format of each script call would be as follows.
```
poetry run python ./script/provision/name_of_script.py input.json output.json
```
Note: Run this script from the root of the project, the paths to your json files need to be relative to where you're running the command from

Each script takes it's `input.json` file, pulls the necessary data from it, makes the appropriate API calls, and the pushes all the info from the `input.json` file along with new information gained from the API calls to the `output.json` This means that the output of each step is everything that's needed for the next step.

You should see output detailing each thing the script is doing, or error details if it fails. Once the script is done, it writes all the input (from the input.json) updated with new values from the script.

If there are no errors, running the below with a valid input.json would be a complete process:
```
poetry run python ./script/provision/a_create_tenant.py input.json tenant_output.json
poetry run python ./script/provision/b_setup_billing.py tenant_output.json billing_output.json
poetry run python ./script/provision/c_billing_profile_tenant_access.py billing_output.json ta_output.json
poetry run python ./script/provision/d_setup_to_billing.py ta_output.json to_billing_output.json
poetry run python ./script/provision/e_report_clin.py to_billing_output.json clin_report_output.json
poetry run python ./script/provision/f_purchase_aadp.py clin_report_output.json purchase_output.json
```

When a script completes successfully, you should see `writing to output.json` as the final output (with whatever output file you provided). Below is what fields to look for in the output after each step to make sure the correct information was gathered:

### a_create_tenant.py
* "creds" should have values for:
  * "tenant_id"
  * "tenant_admin_username"
  * "tenant_admin_password"
* "csp_data" should have values for:
  * "user_id"
  * "tenant_id"
  * "user_object_id"
  * "domain_name"

### b_setup_billing.py
* "csp_data" should have values for:
  * "billing_profile_id"
  * "billing_profile_name"
  * "billing_profile_properties"
    * This should be a nested object with address and invoice section information

### c_billing_profile_tenant_access.py
* "csp_data" should have values for:
  * "billing_role_assignment_id"
  * "billing_role_assignment_name"

### d_setup_to_billing.py
* "csp_data" should have values for:
  * "billing_profile_enabled_plan_details" the body of which should look like this:
    ```json
    {
        "enabled_azure_plans": [
            {
                "skuId": "0001",
                "skuDescription": "Microsoft Azure Plan"
            }
        ]
    }
    ```

### e_report_clin.py
* "csp_data" should have values for:
  * "reported_clin_name"
    * The value of this should look like this: "X:CLIN00Y"
      * Where `X` is the the value of "initial_task_order_id"
      * Where `Y` is the CLIN type (1 or 2)

### f_purchase_aadp.py
* "csp_data" should have values for:
  * "premium_purchase_date" - should be roughly the time/date when the script was run

## Reporting Additional CLINs

The initial process expects a single initial CLIN to bill against, for the purposes of constructing all the necessary Azure resources. After that, additional CLINs, including CLINs for support services. To report these new clins, you need the final output file from the process above (if you used all the examples, it'd be called `purchase_output.json`). You need to add a new section to the bottom of the file, called `"new_clins"`, below is an example (`...` placeholders for filled in values):

```json
{
    "creds": {...},
    "config": {...},
    "initial_inputs": {...},
    "csp_data": {...},
    "new_clins": [{
        "amount": 1300.00,
        "start_date": "2020/02/01",
        "end_date": "2021/02/01",
        "type": "1",
        "task_order_id": "FAKE2"
    }, {
        "amount": 2200.00,
        "start_date": "2020/02/01",
        "end_date": "2021/02/01",
        "type": "2",
        "task_order_id": "FAKE2"
    }]
}
```

Once you've updated the input file, you can run this script like you have previously:

```
poetry run python ./script/provision/report_new_clin.py updated_purchase_output.json clins_reported.json
```

Once you've run this, you should see a new section inside of the `"csp_data"` section of the output json with a string for each CLIN that was successfully reported. If the length of the list does not match the length of the list of CLINs you provided, check the terminal output for any error messages.

```json
{
    "creds": {...},
    "config": {...},
    "initial_inputs": {...},
    "csp_data": {
        ...other fields...,
        "reported_clins": [
            "FAKE2:CLIN001",
            "FAKE2:CLIN002"
        ]
    }
}
```


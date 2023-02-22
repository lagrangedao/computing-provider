## Lagrange docker build pipeline 
As a pipeline, the states are changing according to the build needs.

Standard build process:

* Webhook trigger
* Task creation
  * Task details from CID
  * Download the Space
  * Make build
  * Push to the remote docker hub
  * Clean up
    * build file
    * local cache
    * images

## Lagrange worker queue
* Receive Task from webhook
* Send computing jobs to LAD worker
* Get the computing result back to the cid
  * instance id
  * computing result
# Replicated logs application

This is a prototype of distributed log processor. It contains a Master node and 2 secondary nodes. 
Two endpoints are available on the Master node: \
    - `/append` - adds new log message to the general log storage \
    - `/logs` - returns a list of stored logs
Once the Master node receives a new log, it replicates it on both Secondary nodes.

## Run
In order to build and run the app you can execute a docker-compose command: \
`docker-compose up --build`

After that you can use the Swagger UI to test the app. It is available at the url: \
`http://0.0.0.0:8000/docs`

## App features
* Logs replication is performed asynchronously (using *asyncio* and *aiohttp*);
* Messages are stored and returned to the sender in the same order as they were received;
* Support of `write_concern` options, which specify how many ACKs the master should receive from secondaries before responding to the client
  * `write_concern=1` - only from master
  * `write_concern=2` - from master and one secondary
  * `write_concern=3` - from master and two secondaries 

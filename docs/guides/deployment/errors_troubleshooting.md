# Troubleshooting of possible errors

## Elasticsearch error 400 - search_phase_execution_exception
If you run the detection with the `./mange.py impossible_travel` command and you get the following error:
```
elasticsearch.exceptions.RequestError: RequestError(400, 'search_phase_execution_exception', 'Text fields are not optimised for operations that require per-document field data like aggregations and sorting, so these operations are disabled by default. Please use a keyword field instead. Alternatively, set fielddata=true on [user.name] in order to load field data by uninverting the inverted index. Note that this can use significant memory.')
```
Probably you added the login data on Elasticsearch before the loading of the template. 

Solution:
1. Delete the data from the *Stack Management &rarr; Index Management* section
![image](https://github.com/certego/BuffaLogs/assets/33703137/98c4c22b-36a1-4dc8-9d6c-e8fc5394c26a)
2. Delete the template from *Stack Management &rarr; Index Management &rarr; Index Templates* 
![image](https://github.com/certego/BuffaLogs/assets/33703137/4ffa4fbb-b8d1-4f47-9e02-f4f593f5c124)
3. Load again the template with the `./load_templates.sh` script that you can find in the */config/elasticsearch/* BuffaLogs' folder
4. Recreate the login data using the `python random_example.py` script.


# Reset Docker environment
If you have multiple errors and you'd like to reset all the Docker environment, follow the steps below:
**Docker cleanup**.  
    a. **Delete BuffaLogs image**. See all the images with `docker images ls` and delete the BuffaLogs image: `docker rmi <image_ID`
    b. **Remove containers**. List all the containers launching `docker container ls -a`, then stop the container you want to delete if it's running: `docker container stop <container_ID>` and delete it with: `docker container rm <container_ID`
    c. **Remove volumes**. Visualize all the volumes running `docker volume ls` and remove with `docker volume rm <volume_name>`
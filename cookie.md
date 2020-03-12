# Migrating the database

<!-- https://github.com/pydanny/cookiecutter-django/issues/2444 -->

- Get a database dump, and store it in `.volumes/local_elasticsearch_data`

```bash
pg_dump -O -E utf-8 -U app_ctrs -f ~/stg.sql -h db-stg.ctrs.cch.kcl.ac.uk app_ctrs_stg
```

- Compress the dump file with `gzip`

```bash
gzip stg.sql
```

- Create and start the containers

```bash
./bake.py up --build
```

- Connect to the postgres container

```bash
./bake.py -s postgres exec bash
```

- Check if the database is running

```bash
ps -ef | grep cotr
```

- If there are processes running stop them

```bash
kill ID1 ...
```

- Restore the database using the database dump file

```bash
restore stg.sql.gz
```

- Exit the container

```bash
exit
```

- Run the migrations

```bash
./bake.py manage migrate
```

- [Load Archetype content](https://app.activecollab.com/148987/projects/759/notes?modal=Note-7240-759-0)

```bash
./bake.py manage ctrstxt import path_to/arch-content.json
```

- Create a superuser (LDAP is not enabled in local development, only in production)

```bash
./bake.py manage createsuperuser
```

- Browse to <http://localhost:8000/>

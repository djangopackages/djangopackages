TEMPLATE_FILE="docs-template.md"

docker-compose run django cog -D class_name=DeprecatedRule -o docs/docs/rules/deprecated.md -d $TEMPLATE_FILE
docker-compose run django cog -D class_name=DescriptionRule -o docs/docs/rules/description.md -d $TEMPLATE_FILE
docker-compose run django cog -D class_name=DownloadsRule -o docs/docs/rules/downloads.md -d $TEMPLATE_FILE
docker-compose run django cog -D class_name=ForkRule -o docs/docs/rules/fork.md -d $TEMPLATE_FILE
docker-compose run django cog -D class_name=UsageCountRule -o docs/docs/rules/usage_count.md -d $TEMPLATE_FILE
docker-compose run django cog -D class_name=WatchersRule -o docs/docs/rules/watchers.md -d $TEMPLATE_FILE

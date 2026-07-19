## License

By submitting a contribution to this project, you agree that your contribution will be licensed under the BSD 3-Clause License.

## Development

Install `uv`.

Install `just`.

Install Node.js and [Supabase](https://supabase.com/docs/guides/local-development).

Install Docker. Start the Docker engine.

Create a development env file.

```
cp .env.example .env
```

Edit the `.env` file to include the `Publishable` key from the `npx supabase status` command.

First time only or if you change the seed data, populate the database:

```
just dev-db-reset
```

Run the supabase local development server and the flask development server:

```
just dev
```

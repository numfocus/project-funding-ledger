## License

By submitting a contribution to this project, you agree that your contribution will be licensed under the BSD 3-Clause License.

## Development

Install `uv`.

Install `just`.

Install Node.js and [Supabase](https://supabase.com/docs/guides/local-development).

Install Docker.

Create a development env file.

```
cp .env.example .env
```

Edit the `.env` file to include the `Publishable` key from the `npx supabase status` command.

Run the supabase local development server and the flask development server:

```
just dev
```

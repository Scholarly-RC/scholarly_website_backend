import { createDirectus, authentication, rest, schemaSnapshot, schemaDiff, schemaApply } from '@directus/sdk';

const PROD_DIRECTUS_URL = 'https://directus-production-a710.up.railway.app'; // Production instance URL
const LOCAL_DIRECTUS_URL = 'http://localhost:8055'; // Local instance URL

// Use static tokens if available (recommended for scripts)
// const PROD_TOKEN = 'your_prod_admin_static_token';
// const LOCAL_TOKEN = 'your_local_admin_static_token';

// If using email/password instead:
const PROD_EMAIL = '';
const PROD_PASSWORD = '';
const LOCAL_EMAIL = '';
const LOCAL_PASSWORD = '';

const prodClient = createDirectus(PROD_DIRECTUS_URL).with(rest()).with(authentication());
const localClient = createDirectus(LOCAL_DIRECTUS_URL).with(rest()).with(authentication());

// Authenticate (comment out if using static tokens and use .with(staticToken('token')) instead of .with(authentication())
await prodClient.login(PROD_EMAIL, PROD_PASSWORD);
await localClient.login(LOCAL_EMAIL, LOCAL_PASSWORD);

async function main() {
  const snapshot = await getSnapshot();
  const diff = await getDiff(snapshot);
  await applyDiff(diff);
  console.log('Schema sync complete.');
}

main().catch(error => {
  console.error('Error during schema sync:', error);
});

async function getSnapshot() {
  return await prodClient.request(schemaSnapshot());
}

async function getDiff(snapshot) {
  return await localClient.request(schemaDiff(snapshot));
}

async function applyDiff(diff) {
  return await localClient.request(schemaApply(diff));
}
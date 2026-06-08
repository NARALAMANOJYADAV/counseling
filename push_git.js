const git = require('isomorphic-git');
const http = require('isomorphic-git/http/node');
const fs = require('fs');
const path = require('path');

const dir = process.cwd();

async function run() {
    try {
        console.log('--- Git Status ---');
        const files = await fs.promises.readdir(dir);

        console.log('Staging all changes...');
        // Iterate through all files and add them, excluding .git and node_modules
        for (const file of files) {
            if (file !== '.git' && file !== 'node_modules' && file !== 'venv') {
                await git.add({ fs, dir, filepath: file });
            }
        }

        console.log('Committing changes...');
        const sha = await git.commit({
            fs,
            dir,
            author: {
                name: 'Manoj N',
                email: 'manojnarala245@gmail.com'
            },
            message: 'Auto-commit: pushing changes from Antigravity'
        });
        console.log('Commit successful. SHA:', sha);

        console.log('Attempting to push to origin main...');
        // Note: This will likely fail if a token is not provided.
        // If the user has a token, they can provide it.
        // We will try without authentication first to see the error.
        await git.push({
            fs,
            http,
            dir,
            remote: 'origin',
            ref: 'main'
        });
        console.log('Push completed successfully!');

    } catch (err) {
        if (err.code === 'AuthError') {
            console.error('Authentication Error: A GitHub Personal Access Token is required to push changes.');
            console.log('Please provide a token to proceed.');
        } else {
            console.error('Error during git operation:', err);
        }
    }
}

run();

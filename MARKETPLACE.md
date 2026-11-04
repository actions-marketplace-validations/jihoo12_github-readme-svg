# Publishing the action

The repository includes the root `action.yml`, an Apache-2.0 license, usage examples,
and CI that exercises the composite action on Linux, macOS, and Windows.

1. Push these changes to the public `jihoo12/github-readme-svg` repository and wait
   for **Test Marketplace action** to pass.
2. Open **Releases → Draft a new release**, create the tag `v1.0.0`, and describe
   the initial release (21 SVG styles, multiline text and tags, contribution calendars).
3. Select **Publish this Action to the GitHub Marketplace**. The repository owner
   must accept the GitHub Marketplace Developer Agreement and have 2FA enabled.
4. Check the metadata validation, including availability of the action name.
   Suggested categories: **Utilities** and **Content Attachments** (choose from
   the categories available in GitHub's release form).
5. Publish the release, then create the major-version tag `v1` at the same commit
   so the README's `uses: jihoo12/github-readme-svg@v1` examples resolve.
   Keep `v1` pointing to the latest compatible v1 release. Consumers can instead
   pin the full release commit SHA for an immutable reference.

The action generates files only. Users choose whether to commit, upload, or deploy
them in their own workflows. Contribution styles fetch public GitHub contribution
HTML without a token; banner styles work offline after Python is set up.

Official instructions: [Publishing actions in GitHub Marketplace](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace).

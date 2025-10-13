
# Issue: Unable to delete job description using Playwright

## Summary

When attempting to delete a job description from the application using Playwright, the confirmation dialog appears and then immediately disappears, preventing the deletion from being confirmed. This issue seems to be related to the handling of the confirmation dialog.

## Steps to Reproduce

1. Navigate to http://localhost:3002/.
2. Click on the "Jobs" tab.
3. Click on the "Actions" button for any job description in the list.
4. Click on the "Delete" button in the actions menu.
5. A confirmation dialog appears, but then immediately disappears.

## Expected Behavior

The confirmation dialog should remain visible, allowing the user to confirm or cancel the deletion.

## Actual Behavior

The confirmation dialog appears and then immediately disappears, preventing the user from interacting with it. The job description is not deleted.

## Error Messages

There are no explicit error messages in the console, but the Playwright script fails with a timeout error when trying to click the confirmation button because the dialog is no longer visible.

## Screenshots

*No screenshots were taken, but the behavior is described above.*

## Additional Notes

This issue was observed while using Playwright to automate the deletion of a job description. The issue may also be reproducible with manual testing.

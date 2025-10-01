
I am expecting the app to have a top banner with a logo and primary navigation, a toggle for light/dark mode, and a link to access the user's profile and preferences (such as saying, "hi, [username]!)
A slogan or summary follows on a new line, along with the main tabs of the app.

Then, there may be a alert banner, that can be closed by clicking a X buttonn on the top left corner.

Below this top section, the app will be divided in three sections: a narrow, permanent left panel, a narrow right panel that can be hidden, and a central main panel.
The central section will either be a large section with multiple cards, split in two side panels, or a dual-panel view, depending on the tab.

Since the site will be mostly accessed using desktop computers, the large format screen should be the primary focus of the UI development.

## 1. Dashboard
The dashboard is displayed as a left panel on the landing page of the application, and must show visually the overall status, statistics, and recent activities in the application. it must include
    *   **Statistics Card**: Key metrics such as the total number of jobs by categories. clicking on each categories should link to a more detailed Statistics page
    *   **System health Card**: Key metrics on the system's performance and usage. Clicking on high-level indicators should link to a more detailed System health page that allows administrators to monitor the health and performance of the system and to identify trends and patterns in user activity.
    *   **Recent Jobs List**: A list of the most recently accessed or modified job descriptions.

## 2. Jobs
*   **Display**: The jobs screen is accessible directly from the landing page of the application, in the main center panel. when clicking the "View Jobs" button in the panel, the screen should display a detailed table of all the job descriptions in the database. Each job should be displayed as a line in the table with key metadata such as the job ID, status, high-level quality indicators, classification, and language. A button at the top of this view should allow user to upload new jobs to the database, or create new, or go to an advanced search page. clicking on each job would lead to a detailed view of the job, which each section of the job description displayed as cards. This view should include buttons to interact  with the job description: Editing, Approve, duplicate, Translate, Compare, export, archive.

## 3. Editing
*   **Display**: The basic editing screen is a multi card workspace where each section of the job description is displayed, separately, for users to edit, modify, and save changes to the content of the job description. This screen contains buttons to save, approve, and undo changes, as well as a button to access the advanced editing screen. the Editing view can be used collaboratively by multiple concurrent users.  It also displays:
    *   **User Presence**: Avatars of all users currently active in the session.
    *   **Collaborative Cursors**: The cursor position of other users in the editor.
    *   **AI Assistant Panel**: A panel that displays AI-powered suggestions for improving the content.
    *   **Properties Panel**: A panel that displays information about the job description as well as measures of accessibility, language bias, and quality scores for the job description, as well as bullet point suggestions to improve the scores.
Both the AI assistant panel and the properties panel are on the right side of the job description, with the properties panel on top and the AI assistant panel below, and both can be displayed or hidden using a toggle.

 ## 4. Advanced Editing
the advanced editing screen features a dual-pane editor with the source document (current saved version) on the left and the target document on the right. When a user access the advanced editing screen, a warning to the user is displayed and it locks the job description for editing by other users. Accessing the advanced editing screen triggers the use generative AI to draft an improved job description version, called the target version. The target version is created using the currently saved job description as a basis, and by using generative AI to improve it iteratively using multiple prompts, reviewing each section against the others for concurrence and alignment, and using best practices and compliance rules from the job description drafting guide, style guide, departmental context and other saved job descriptions as well as other factors to improve the content of the job description. In this view, the user can make changes directly to the saved version in the left panel, save the modifications to the database, and re-trigger the AI generation. The user can also modify the generated content in the right panel, access variations of ai-generated content by right-clicking on selected text, pick and choose the most appropriate version, or trigger changes to the target version by entering instructions in a text box and clicking a button. when the user accepts the target version, it is saved as a new version of the same job in the database and the system uses AI to understand how the user improved the content of the job description and the AI-generated content, and uses reinforcement learning from human feedback (RLHF) to align the JD improvement intelligent agent with human preferences.

## 5. Advanced Search

*   **Display**: The search screen provides a powerful interface for finding job descriptions. It includes:
    *   **Search Input Field**: A text box for entering search queries.
    *   **Filter Controls**: A set of filters for narrowing down the search results by classification, language, department, and other criteria.
    *   **Search Results**: A list of job descriptions that match the search query, with highlighted matching sections.
*   **Functionality**: The search screen allows users to perform both basic keyword searches and advanced semantic searches. Users can also save their search queries for later use.

## 6. Upload

*   **Display**: The upload screen provides a simple interface for uploading new job descriptions. It includes a drag-and-drop area for files and a list of supported file formats.
*   **Functionality**: Users can upload one or more job descriptions in various formats, and the system will automatically process them and add them to the database.

## 7. Compare

*   **Display**: The compare screen allows users to compare two job descriptions side-by-side. It displays the content of the two selected job descriptions in a dual-pane view, with differences highlighted. a third panel, on the right side, displays indicators of quality, improvement metrics, as well as AI settings and preferences.
*   **Functionality**: Users can select any two job descriptions from the database and compare them to identify similarities and differences. users can also click a button to merge both jobs together, which navigates the user to an editing page with a new, AI generate version based on a composite of both compared roles. before moving to that new screen, the system will ask the user if the merged version is meant to replace the two previous versions, include the content of one of the job into the other, or create a completely new hybrid role. In any of these cases, a note will be added to each JD mentionning the parent/child relationships between the versions, and the status of each JD will be modified to reflect the tentative merger.

## 7. Translate

*   **Display**: The Translate screen allows users to review the English and French versions of a job description side-by-side. It displays the content of the job descriptions in a dual-pane view, with the original language on the left and the translation on the right.
*   **Functionality**: Users can select any job description from the database, and both languages of the job description will load. If the job description has not been translated yet, the right panel will be empty: the user can click "translate" and the AI will generate a translation in the second official language. users can right click on selected words or text strings to review suggested alternate translations or select and compare them to identify similarities and differences. changes made to either language content will be highlighted on the opposite side, and once the translation is finalized by the user and the user confirms concurrence between versions, both language versions will be saved in the database with the status translated.

## 8. Statistics

*   **Display**: The statistics screen provides a detailed overview of the system's database content and usage. It includes metrics such as the total number of jobs, processed documents, and recent activity.
*   **Functionality**: The statistics screen allows administrators to monitor the health and performance of the organization and to identify trends and patterns in user activity.

## 9. System

*   **Display**: The System screen provides a detailed overview of the system's performance and usage. It includes metrics on recent activity, AI interaction, and system health.
*   **Functionality**: The System screen allows administrators to monitor the health and performance of the system and to identify trends and patterns in user activity.

## 10. Preference

*   **Display**: The Preference screen provides a detailed overview of the user's settings. It includes role, preferred language, preferred AI model, and metrics on activity.

## 11. Modern UI This tab will be removed once the modern component of the screen will be incorporated in the other screens

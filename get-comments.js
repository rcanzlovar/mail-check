// get-comments.js 
// Bob Anzlovar 23-oct-2025
//
//
//
async function loadCommentsFromSlug() {
    // Get the current page's slug (last part of the URL path)
    const pathParts = window.location.pathname.split('/');
    // Removes empty strings and gets last segment
    const slug = pathParts.filter(part => part).pop(); 

    // Build the external URL using the slug
    //const externalUrl = `https://rcanzlovar.com/comments/${slug}.html`;
    const externalUrl = '/comments/' + slug + '.html';

    try {
        const response = await fetch(externalUrl);
        if (!response.ok) {
            throw new Error('Page not found: ${response.status}');
        }

        const html = await response.text();

        // Extract content between <body> and </body>
//        const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
//        const bodyContent = bodyMatch ? bodyMatch[1] : "No body content found.";

        // Display the content inline
        //document.getElementById("external-comments").innerHTML = bodyContent;
        document.getElementById("external-comments").innerHTML +=  html ;
    } catch (error) {
        console.error("Error loading external comments:", error);
        document.getElementById("external-comments").innerHTML = ("<h4 class='nav-bar-title'> Be the first to comment!</h4>");
    }
}
// Run the function when the page loads
loadCommentsFromSlug();

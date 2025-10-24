# mail-check - Commenting for static HTML websites 

## Functionality overview

The goal was to make it possible for people to leave comments on a static HTML website 
that would be visible for 
other users. I used to use WordPress until it was hacked due, most likely, not running the 
latest version of WordPress. This solution uses no PHP. The backend is a python script 
run from a bash script with a recurring scheduled task. 


The solution I came up with involves having each blog entry having a unique "reply via email" 
button. The link uses the mailto: HTML tag with preloaded to:, subject: and body= 
parameters. The email is a dedicated mailbox with a name like comments@myblog.com. The 
subject contains the name of the "slug" along with the subject line. The "slug" is the 
part of the URL of the posting that has the name normalized removing punctuation and 
providing dashes where spaces or punctuation was. For instance, if the subject was 
"how to roller-skate" the slug would be "how-to-roller-skate". On the reply email, the 
subject would be 

Subject: (how-to-roller-skate)How to roller-skate

The bodis preloaded as well with some instructions to put the comment between two lines 
of dashes. 

Once the email is written and sent, it waits in the mailbox of the comments email user. 
I wrote a python script which runs every 10 minutes to check the mailbox. If a new message is found, 
the script downloads it, extracts the email, date, subject and body of the message. I save 
the raw email in case I need to use it to recreate the comment content, Based on the slug, 
I either create or append a file with that name ending in .html 

If changes were made, then the script uploads the content of the comment directory to my website to a 
directory which is not linked to anything. In case anyone ever figures it out, I have an index.html that 
instantly redirects to the home page. 

When the blog entry page loads, a javascript function checks that directory on the website for a page in the comments 
directory that has the same name as the 
slug.  If such a page is found, it's downloaded by the javascript and its conents are inserted 
into the a div in the blog entry page on the fly. 

All of the interactivity happens in the client browser. The only executable code runs on a system in my home. This 
feels a little bit fragile, but given my experience of having been hacked, I like it. A job on the hosting website 
could be used but then the private information (passwords for the scp, IMAP and SMTP) would reside on the server 
on the internet. These values are contained in a config file, also on my local machine, so the passwords and such 
aren't hard-coded in the script. 

The job that polls for email and uploads is controlled by a systemd daemon. The old school way to do this would 
be a cron job. 

# Upcoming functionality

Currently this will accept comments from anyone. I plan to implement a "whitelist" of email addresses who are allowed
to post. First time someone posts, It will probably end up being a SQLite database or something similar running on the 
same system as the checkmail script. Once someone is added, they can post whatever they want. I currently have no 
plans for post-by-post moderation. I just don't have that many readers yet. 

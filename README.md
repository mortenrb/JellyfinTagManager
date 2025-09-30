# JellyfinTagManager
Just a simple Tag Manager for Jellyfin.

I got annoyed from editing one and one tag for movies and shows via the Jellyfin GUI, so I made a simple tag manager that allows for batch editing of tags.

It's just a quick and dirty program made from painfully ripping out my hair because nothing the AI did worked, so I still had to do manual labour.

The pip version of jellyfin_apiclient_python (1.11.0) isn't working properly because of changes to BiggerAPIMixin.items() and InternalAPIMixin._post() functions, you're better off using the version from their repo https://github.com/jellyfin/jellyfin-apiclient-python or manually updating those two functions.

![Screenshot of the software in action](https://raw.githubusercontent.com/mortenrb/JellyfinTagManager/refs/heads/main/image.png)

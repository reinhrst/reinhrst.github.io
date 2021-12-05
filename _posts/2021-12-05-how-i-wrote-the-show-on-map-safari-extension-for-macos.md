---
title: 'How I wrote the Show on Map Safari Extension (for MacOS)'
categories:
    - tech
    - manual
tags:
    - howto
    - safari web extensions
    - safari
    - xcode
toc: true
header:
    image: /assets/images/2021/12/05/teaser.jpg
---

A couple of weeks ago I had to look for a company to rent some Nerf guns from, for a long weekend in the Ardennes with friends. There are several companies in The Netherlands and Belgium doing just that, but I wanted to find one that was on the route. I found myself copy-pasting city and village names into Google Maps to find where all these places were located.

Was this unworkable? No.
But was it slightly annoying? Yes.
So as I good nerd, I decided to create [a solution](https://show-on-map.claude-apps.com/).

Last year I created [my first Safari Web Extension](https://apps.apple.com/nl/app/smart-keyword-search/id1541221580), Smart Keyword Search. Safari Web Extensions were launched at WWDC 2020 for Safari 14. Before this there were only Safari App Extensions (and before this Safari Extensions; this naming makes for great Googling, especially since sometimes even Apple doesn't use these names consistently).

<div class="notice" markdown="1">
It turns out that so far that either the need for this Safari Extension is not so large, or people don't know how to find it.
In the first month of it being online, it has been downloaded a grand total of 5 times from the App Store (including once me installing it myself), and it has not seen much use either.
All installations were in the first week; which may have had something to do with me starting to ask &euro;1 for it starting the second week.
This was just for fun; this app is never going to make serious money, however I very much liked the idea of being able to say, at the end of a week of hard work, that my beer was paid for by the app.
In hindsight, I should probably be happy that nobody downloaded the paid-for version; I'd hate to have to figure out tax stuff because of a handful of euros....

I just changed the settings back to make the app free again.
</div>

<div class="notice--success" markdown="1">
This post is one of those that I write mostly as a note to future-me.
I include a lot of stuff that I learned over the process of doing something, and I know myself well enough to realise that I will forget some of the details.
It does not mean at all it's not useful for other people; actually [the most-read and most-appreciated post on this blog](./2020-10-01-Setup-Neovim-as-Python-IDE-with-virtualenvs.md) is one that I wrote mostly with future Claude in mind.

If you came to this page looking for a walk-through of how to build an extension step by step, I'm sorry, this is not it.
On the other hand, it is meant to be a more or less story from start to end (rather than just random statements) and there are many (I think useful) tidbits of information on this page, which I hope Google will serve up to those looking for it.
</div>


# Safari Web Extensions - the basics
Safari Web Extensions (as launched at WWDC 2020) are based on the Browsers Extensions standard ([MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions); the terms Browsers Extension and Web Extension seem to be used interchangeably on MDN), written in HTML and JavaScript, which is also used in Firefox and Chrome extensions (whereas the older Safari App Extensions are written in Swift/Objective-C). But whereas Chrome and Firefox extensions are a standalone bundle of HTML/JS/etc, Safari Web Extensions always consist of three parts: An HTML/JS/etc part, a native part of the extension and a native app. Understanding these parts helps to understand the possibilities and limits of Safari Web Extensions.

Note that in this context it might also be useful to read the [MDN description of the anatomy of a Web Extension](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Anatomy_of_a_WebExtension), which explains how the part that we call the HTML/JS/etc part of a web extension looks.
A certain knowledge of this is expected later in this post.

I should mention that this description is true for Safari Web Extensions for MacOS. At WWDC 2021 Apple announced Safari Web Extensions for iOS 15; quite some things in this blog should apply to that as well, but I don't know (yet) exactly what is the same and what is different.
{: .notice}

## Parts of a Safari Web Extension

### Native app
Let's first talk about the native app, since this is easiest to understand. The native app starts and stops like a normal app; start by clicking it from the /Applications folder, and end it with `cmd-Q`. When you start a new Safari Web Extension in Xcode, it comes with a standard native app, that just shows a button to open the settings page in Safari where extensions can be installed. In my experience you see this app only right after you install it, it directs you to the settings page where you enable the extension, and then you never use it again.
On the other hand, this app can (obviously) be as complex as you like; for example Bitwarden has a native app that allows you to manage your passwords, while the Safari Extension fills in the passwords in the browser.

I don't have an authoritative source, but I think should be possible to make a Safari Web Extension without a native app part, however I don't think it gets into the App Store. I did submit multiple app Safari Web Extensions to the App Store where the native app was just the default app that Xcode generates for you, only with the icon replaced.

### HTML/JS bundle
The second part we talk about is the HTML/JS/etc bundle. This is the part that runs in the browser, interacts with the browser, and where you should definitely write something interesting if you want your extensions to do anything at all. As discussed before, this part is based on the Web Extension standard and MDN has great documentation, including what is and is not supported in Safari.

The lifetime of this part depends on a lot of factors; background scripts can be persistent (meaning they start and stop with the browser) or not-persistent (meaning they run only when needed). Browser actions (a small page that pops up when you click the extension button in the address bar) start and stop with this pop-up page opening and closing, etc. Important though is that they run completely independent from the native app.

### Native part of the extension
Then finally there is the native part of the extension. Even though I wrote my first extension a year ago, I only recently learned about this part. It's part of the extension, but written in swift (or objective-C I guess). 
It doesn't have a UI, and as far as I know all it can do is receive messages from the HTML/JS part and do things that are not possible in HTML/JS.
To me it's a bit unclear when it's starting and ending, however it's always there when you send a message (it might start and stop with Safari, or start when a message is received, and stop when the reply is sent; important is that this is not the developer's worry).

## Messages
We just discussed the possibility of sending messages between the parts. It took me some time to understand how this works exactly.

<div markdown="1" class="notice">
There seems to be a difference in how Chrome/Firefox does native messaging and how Safari does it. I don't have experience doing this in Chrome/Firefox, but it seems that you can connect to an arbitrary other application defined in some JSON file (obviously this application needs to accept and understand your messages or else the connection is useless).

In Safari you can connect to one native app, and one only: the one that the extension shipped with. This is nice in that you can trust that messages you send are not eavesdropped on, and that messages you receive are from your own app/extension. (I'm sure there are also use cases where this restriction is problematic, I'm not claiming one method is better than the other, just pointing out a large advantage).
</div>

There are 2 ways of messaging native apps; [on MDN these are called connection-based and connectionless](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging); on Safari there is a large difference between these two methods (unlike what is suggested by MDN, making me think that this is not true for other browsers). Note that if you want to use either, you must have the `nativeMessaging` permission set in your `manifest.json`.

The connection-based messaging (`port = browser.runtime.connectNative()`) connects to the native app. This function has to be called from the HTML/JS part and will only work if the native app is running. After this connection has been made, messages can be sent either way.

The connectionless method (`browser.runtime.sendNativeMessage`) on the other hand allows sending a single message from HTML/JS to the native part of the extension, and get a single reply back. Because the native part of the extension is part of Safari, there is no need for it to be running. Only the HTML/JS part can initiate a message exchange; it cannot be initiated from the native extension part.

Supposedly (but out of scope for this post) the native part of the extension and the native app can also communicate with each other.

<div markdown="1" class="notice">
Right here we only discuss communication between HTML/JS and native parts. I'm addition there are `browser.runtime.postMessage` (send messages between different parts of the HTML/JS part, such as the background page and the browser action (small pop-up page)), `browser.tabs.sendMessage` (talking between the HTML/JS part and a ContentScript that the extension inserted into the page), and `window.postMessage` (sending messages between different iframes or windows). For every `postMessage` there is also a `Connect` for connection-based communication.

As long as I'm here, a word of warning (something that took me many many hours to find out myself). The `onMessage` event handlers that receive the messages can, [according to MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/runtime/onMessage#addlistener_syntax) return a Promise which, when fulfilled, will send a response back to the sender of the message.
As shown in the [Browser Compatibility Matrix](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/runtime/onMessage#browser_compatibility), Safari doesn't allow for this, and needs to use the `sendResponse` argument (yes, I know, RTFM, but still, it took me forever to debug why I was not getting a reply).

It's unfortunately not the only time that Safari seems to not implement small parts of the spec; just beware when you're writing your code.
</div>

## Interaction
An extension is obviously only useful when it does anything, when it has some sort of interaction with the system and/or the user.
There are many ways in which extensions can interact; some common ones are showing something when the user clicks the "BrowserAction" (this is the little icon that appears next to the Safari address bar) or intercepting / altering requests (this is actually exactly what my previous extension did).

The Show on Map extension main interaction is through the context menu; when one right-clicks on a word, Safari selects that word (unless something is already selected), and shows a little menu.
Extensions can add items to that menu (and, according to the spec, an icon, however Safari doesn't support the icon).
Show on Map adds a menu item called `Show '%s' on a map`; Safari will automatically replace the `%s` with whatever is selected, adding ellipses when needed.

Show on Map also has a BrowserAction, this is because I haven't figured out yet how to disable the BrowserAction completely.

Version 0.5 of the extension would, when "Show XXX on a map" was clicked, open an overlay in the page, with an iframe showing yet another iframe showing Apple Maps through MapKit JS (I explain this complicated setup below, feel free to skip it unless you're either a masochist or are looking for exactly that information.
After trying to get it approved by Apple, and them replying that it didn't work for them, I decided that there were too many moving parts in this setup (including the fact that MapKit JS was still in beta), and moved to a simpler setup.
In version 1.0 (which is the one that got approved and is currently in the App Store), right clicking on 'Show XXX on a map" results in the Apple Maps app being opened (as far as I know, Apple Maps is always installed on every modern Mac).

Opening Apple Maps from the browser is easy (just follow <a href="http://maps.apple.com/?q=Haarlem,Netherlands" target="_blank">this link</a> to see my home town), however (at least on Safari on a Mac), it has the nasty side effect of asking permission to open the Maps app, and leaving the user with an empty tab; the extension could close the empty tab after use, but still it's far from the seamless experience I was aiming for.

From a native app however you can open the Apple Maps App without an extra warning or opening a new tab in Safari, so the solution was to have the native part of the extension open the Apple Maps App.

<div class="notice" markdown="1">
Two side notes. Firstly, it's probably a good idea that webpages can not just open a location in the Apple Maps app without your permission, you don't want a browsing session to leave you with some random address in Apple Maps.


Secondly, why use Apple Maps and not Google Maps, which seems the go-to maps provider.
Even though I like Apple Maps better from a privacy standpoint (DuckDuckGo used to use Apple Maps before it switched to OpenStreetMap), there was a practical matter.
In version 0.5 I wanted to open a map in-page; both Apple and Google require you to use an API with API key to do just that; I found it easier to get an Apple API key (since I already have an Apple developer account) than a Google one.

There was always an idea that if the extension proved a success, different maps providers could be built in; that would be even easier in version 1.0, since adding Google would just mean opening a new tab with a Google Maps URL (no API key is necessary in that case).
</div>


# The Show on Map app
Basically the extension needs to do a couple of things:

- Have a way for a user to define what they want to search for. &#9989; using selection and context menu, we provide this
- Do an intelligent search and find a place. Searching is less straight forward than one might imagine; when searching for "San Francisco, CA, USA" there is probably not much doubt what you're looking for. But what if you search for Paris (might depend on whether you're in Europe or Texas), or Perth (different when you're from Scotland, Ontario, Australia or probably a dozen other places around the world). Worse even when looking for "main street", or "Burger King". Ideally a search system may know a lot about you, and do the right thing automatically; it might know that you're planning a trip down under, or that you just read a news story about Amsterdam, NY. (Or at least, this would be ideal if that was all the search system was using your data for \*cough\*-\*cough\*). At the least, having an idea of your current position will probably lead to better search results in most cases.
- Have someone draw you a map, and show it. Again it would be great to know your user; looking for a small village around where you grew up, you could show a map of the village and 2 or 3 surrounding villages; however another person might want to see a zoomed out version, so that they could see where the village is related to the rest of the country. Again current location could be a useful proxy; something like "show a map that covers both the location I'm looking for, and a point halfway between here and there" seems like a useful thing to have (note that Show on Map never did that, I'm just saying that something like that might be something that is useful in most cases).

## Version 0.5
Here I describe version 0.5 of the extension.
As described above, this version opened a MapKit JS overlay within the page.
Many lessons were learned in the process, hardly any of which were useful for the final product.
The following section is mostly to document those lessons, in case someone finds them interesting (or in case I need them later).

<figure class="half">
    <img src="/assets/images/2021/12/05/mark-twain-example.jpg">
    <img src="/assets/images/2021/12/05/longest-example.jpg">
    <figcaption>Showing v0.5 in action, finding Mark Twain and Muckanaghederdauhaulia</figcaption>
</figure>

### Using MapKit JS
Apple has a [JavaScript version of MapKit](https://developer.apple.com/maps/web/), that ought to be suitable for both the things we need to do: GeoSearch (transforming a text into one or multiple map coordinates), and showing a map of just those coordinates.
All you need is an Apple Developer account (something you already have if you're developing for the app store), and you can create an API key that can be used for something like 25000 maps a day.
Apple even very helpfully mentions that if you need more, all you have to do is contact them (suggesting, at least to me, that it's not a question of price, it's just that they want to make sure you're not doing anything bad with it).

It's a bit unclear to me whether MapKit JS is still in Beta or not; some documentation pages [have a beta marker](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging), others [don't](https://developer.apple.com/documentation/mapkitjs).
I did run into some issues though (note that this was in September 2021, things may or may not have changed by now).

#### `mapkit.Search` - `getsUserLocation` option
[`mapkit.Search` has a property `getsUserLocation: boolean`](https://developer.apple.com/documentation/mapkitjs/mapkit/geocoder/2973885-mapkit_geocoder).
The idea is that it will get the user's location and do the Search relative to it (so supposedly preferring local objects to further away ones).
In my tests this worked only very sporadically; I constantly had experiences where I would look for some company name, and would get only results in some small town in the US, or even more often on [Null Island](https://en.wikipedia.org/wiki/Null_Island).

The work-around was not that hard (I hoped...), one just has to use JavaScript to get the location of the user, and then provide that to the `coordinate` property of `new mapkit.Search()` (which, according to the [documentation](https://developer.apple.com/documentation/mapkitjs/searchconstructoroptions/2991282-coordinate) is "A map coordinate that provides a hint for the geographic area to search").

#### `mapkit.Search` -- `coordinate` option
Alas, things did not get better proving a `coordinate` to `new mapkit.Search()`; it seemed that this value was completely ignored.
No worries, `new mapkit.Search()` just creates the search object, we then have to call the `.search()` method, which also has a `coordinate` property..... which also did not work for me.

The final workaround that did work is to add a [`region` parameter](https://developer.apple.com/documentation/mapkitjs/searchconstructoroptions/2991285-region), which is "A map region that provides a hint for the geographic area to search".
A region is an rectangular area (as much as that is possible on the surface of a sphere) that is the given number of degrees wide and long, around the given coordinate.
An area of size 0.1 x 0.1 degrees worked for me:

```
const region = new mapkit.CoordinateRegion(homeLocation, new mapkit.CoordinateSpan(0.1, 0.1));
```

#### The MapKit API key and a Safari Extension
In your Apple Developer Account you generate an API key (or you can also choose to generate it locally by signing a JWT with a master key).
You can make an API key that works on a single origin (for instance: `http://show-on-map.claude-apps.com/`), or a wild card key that works everywhere.
The wild card key is not advised to be used outside of development (for the obvious reason that this key is visible to everyone, and can be stolen and used by someone else on their website for things that Apple doesn't like -- and then your account gets blocked; at least this is what I think happens, I didn't try).

A Safari Extension runs on a unique URL, which changes every time Safari is restarted; this supposedly is a security precaution so that a website can never point to a specific Safari Extension.
The URL looks something like this: `safari-web-extension://1e70cb50-300c-47b7-898c-5c082f836d7d/`, with the guid being different every time.
That's great for security, however it does mean that it's not possible to generate an API key for maps that works, unless it's a wild card key.
Also trying to limit the key to only Safari Web Extensions (something like creating a key for `safari-web-extension://*` does not work.
I [asked a question about this on the developer forums](https://developer.apple.com/forums/thread/691380) but no answer as of yet.

#### The MapKit API key and expiration
The API keys you generate for MapKit JS have a maximum validity of one year.
This means that if you ship your extension with an API key built in, you will have to ship an update in 9 months, and hope that everyone will update in the 3 months afterwards.
You should be able to create multiple API keys (if you sign your JWT manually), each one valid for a year with a couple of days overlap (so one valid until 10 November 2022, then one valid until 8 December 2023 (so from 9 December 2022), etc, and choose the right one based on the system date (I didn't try it, but I don't see why it shouldn't work), it just makes things exceedingly complicated.

My conclusion (for the last 2 items) is that MapKit JS probably works well on websites, but it's not useful at the moment in extensions (I still tried it though in v0.5).
It would be interesting to investigate if Google Maps has the same limitations (but I didn't).

### Where and how to show the map
Initially I wanted to show the map in the BrowserAction, so the moment you select "Show XXX on a map", the small extension window pops up and shows the map.
It would be the cleanest way I could think of to show the map, without having to change the HTML page you're looking at (with all the potential problems that may bring).
This plan got shot down quickly when I realised that [`browseraction.openPopup()` is not supported in Safari](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/browserAction/openPopup).
In Safari the only way to show the BrowserAction is if the user clicks the icon for the extension in the toolbar, and asking the user to first click "Show XXX on a map" and then having to click again to show the map, is not a nice flow (the moment you click the BrowserAction, it also deselects whatever you have selected on the page in most cases (I forgot the exact details on when this did and did not happen); so getting rid of the context menu all together and have someone select an address on the page and then click the BrowserAction did not work either).

The second plan (that made the cut) is to alter the HTML on the page, add a layer on top, and show the map there.
An extension can add a ContentScript to a page, this is a JavaScript file that gets loaded into the HTML page you're viewing.
This ContentScript can then do lots of interesting things, among which alter the DOM, and add an overlay.

So we're on the right road, if it wasn't for one little bump: the [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP).

#### Content Security Policy
The idea behind of Content Security Policy (CSP) is simple and worthy: it's [an additional layer of defence][1] against hackers.
For instance (and we might go a bit too much into details here, feel free to skip), your website may be programmed to write something like (DON'T DO THIS, it's an example of what not to do):

```
<script type="module" src="https://www.myhost.com$SCRIPTPATH.js"></script>
```

If the hacker somehow manages to make `$SCRIPTPATH` to be `.evil.com/evilscript`, the result now is `https://www.myhost.nl.evil.com/evilscript.js`, and you have an evil script running on your website -- probably something that you would want to avoid.
There are many other bugs that can lead to similar script injections; the important thing is that CSP is the thing that comes into play after your first layer(s) of defence break(s) down.

The Content Security Policy says (in a simple form): `script-src: https://www.myhost.com/`, and as a result only scripts from that URL can run, so the hacker's script will be blocked.

Beyond this there are refinements, limiting what CSS can be loaded, blocking inline scripts (actually the statement above already does that), blocking images, AJAX calls, etc.
The policy (the P in CSP) is delivered either via an HTTP header or in a `<meta>`-tag in the HTML of the page.

Obviously such a defence would be a lot less useful if a script could alter it or switch it off after the page loads, so this is not possible.

A lot of (good/large/run by a company or a competent webmaster) sites have a restrictive CSP set.

[1]: https://en.wikipedia.org/wiki/Defense_in_depth_(computing)
#### Content Security Policy and Extensions (or: CSP and Show on Map)
You might ask yourself by now how a ContentScript can work at all on a page with CSP switched on.
The whole idea (or: one of the ideas) behind CSP is to _avoid_ JavaScript being added to a page from a source not explicitly allowed by the web page creator.
It seems however that extensions are exempt from these rules; a ContentScript is always allowed, even if the page developer doesn't like this (which is good I guess, else lots of pages might block all extensions).

So adding the ContentScript to the page works, altering the DOM to add a layer works, but things added by the ContentScript are _not_ exempt from the CSP.
So if the ContentScript asks for a script to be loaded from `https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.js`, the CSP will block it.
We could get one step further by bundling this script into our extension, but then, as soon as the MapKit JavaScript wants to contact Apple's Map servers (to check the key, so the GeoSearch and retrieve the map tiles), it's blocked again.

<div class="notice" markdown="1">
I should admit that I didn't test this theory to see what exactly is and is not possible;
It seems that the ContentScript runs in a different sandbox from the rest of the JavaScript on the page.
I know the ContentScript cannot add `<script>` tags to the HTML and have them be executed outside of CSP rules, but maybe it could load another script into its own sandbox.
Possibly this script would be able to make AJAX calls outside of CSP rules, or load images, etc.
If not, I guess one could even go a step further and proxy all calls through the BackgroundScript.

It might definitely be something that could be a whole blog post by itself: how does CSP work with Extensions, and what can we do from within an extension to work around the restrictions.
I'll leave it as an exercise for the reader :).
</div>

There is a way to break out of the CSP: if you have an `<iframe>`, the _content_ of the iframe can set its own CSP which is not limited by the parent's CSP.
It may feel like a bug, but it's actually [part of the HTML specification](https://stackoverflow.com/a/43237443/1207489) (so people thought long and hard about it, I'm sure!).

Note that although the content of the iframe is not controlled by the parent's CSP, whether or not you can _load_ that content _is_ controlled (by the `frame-src` directive among others).
Here we can take advantage of the fact that the extension is not blocked by CSP, so we open a page hosted within the extension in an iframe.
CSP defeated!

#### Getting the user's location
Webpages can use the [GeoLocation API](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API) to retrieve a user's location (or more precisely: to ask a user permission to their location).
Permission can often be given to share your location once, or forever; in the latter case the browser remembers that a certain location (such as `https://show-on-map.claude-apps.com/`) has permission to get the location when asked for, and the page will appear under the "Location" tab in the Websites settings menu in Safari.

This does not work for the extension; as mentioned before, the extension is on a different URL on each Safari run, so giving permission forever doesn't work.
In addition, it might be tedious to explain to users *why* you need their location, if all they do is look is a GeoSearch (I definitely know that I refuse Google access to my location more often than not when searching).

I tried a workaround where the BrowserAction page would contain settings, would ask for your current location once and store it, and then use that until changed.
Unfortunately the BrowserAction page [has no way to use the Geolocation API](https://stackoverflow.com/questions/69744402/how-to-get-a-users-geolocation-from-within-a-safari-web-extension), not even with the user's permission.

Finally I looked into the BrowserAction sending a message to the native part of the extension, asking it to get the current location; it was unable to get the current location as well, most likely because it has no UI, so it cannot ask the user for permission.
Something I only thought about as I write this, and what I haven't tested yet, is that if the native application when first opened asks for permission, maybe this will extend to the native part of the extension as well....

#### Conquering the last two hills
Even though we can show the Apple Map (through MapKit JS) in our iframe, we have two problems left.
First, we already mentioned that the only way we could access MapKit JS from the extension, is by generating a wild card API key, something we don't really want to do.
Secondly we run into a problem requesting the user's location.
Luckily both can be solved with a single solution.

The solution is to have the iframe (the one hosted by the extension) open _another_ iframe on a domain that you own (let's say `https://show-on-map.claude-apps.com/`).
This page will contain all the magic: use MapKit JS (with an API key tied to this domain) to make the requests, request the user's location (once, and if permission is obtained forever we never bother the user again).

Since it's opened from within the iframe hosted in the extension, the outside page's CSP doesn't apply.

### Bringing it all together

Bringing this version together, we have the following parts.
<details markdown="1">
<summary>All JavaScript is written in TypeScript; I use the following config (click to open this and other code blocks)</summary>
`tsconfig.json`
```json
{
    "compilerOptions": {
        "outDir": "./build",
        "sourceMap": false,
        "strict": true,
        "noImplicitReturns": true,
        "noImplicitAny": true,
        "module": "esnext",
        "declaration": false,
        "moduleResolution": "node",
        "target": "es2017",
        "allowJs": true,
        "esModuleInterop": true,
        "typeRoots": ["node_modules/@types", "node_modules/web-ext-types"]
    },
    "include": [
        "*.ts"
    ]
}
```
</details>

<details markdown="1">
<summary>The manifest configuring the plugin</summary>
`manifest.json`
```json
{
    "manifest_version": 2,
    "default_locale": "en",

    "name": "__MSG_extension_name__",
    "description": "__MSG_extension_description__",
    "version": "1.0",

    "icons": {
        "48": "images/icon-48.png",
        "96": "images/icon-96.png",
        "128": "images/icon-128.png",
        "256": "images/icon-256.png",
        "512": "images/icon-512.png"
    },

    "background": {
        "scripts": [ "background.js" ],
        "persistent": true
    },

    "browser_action": {
        "default_popup": "popup.html",
        "default_icon": {
            "16": "images/toolbar-icon-16.png",
            "19": "images/toolbar-icon-19.png",
            "32": "images/toolbar-icon-32.png",
            "38": "images/toolbar-icon-38.png"
        }
    },
    "web_accessible_resources": ["applemap.html", "applemap.js", "shared.js"],

    "permissions": [
        "menus",
        "activeTab",
        "storage"
    ]
}
```
</details>

A couple of quick words about the [manifest](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json).
- I defined the background script as persistent.
Since Safari 15 it's possible to use a non-persistent background script, meaning the script will unload while not being used (and hence save resources).
It was on my to-do list to get this to work, but I didn't quite yet dive into which parts were persisted and which not, so I decided to leave it persistent for now.
- The extension needs some permissions.
It needs both `menu` and `activeTab` before it can add an item to the context menu.
I think this is a bit weird, especially from a security point of view; I feel that `activeTab` should only be needed when we actually want to do something in the active tab.
In this version 0.5 of the extension we need `activeTab` anyways because we will add a ContentScript to the active tab, however in version 1.0, the one in the app store, all we want is show a context menu and get access to the selected word; the `activeTab` permission means that we have unlimited access to anything happening in the active tab, as soon as someone selects our context menu item.
The `storage` permission allows us to store the settings that one makes in the BrowserAction.
- In `web_accessible_resources`, I define a couple of scripts that can be accessed from within normal browser context.
Normally the scripts we have (like `popup.html` or `background.js`) can only be referenced in special contexts.
For instance, I can get the URL of the `popup.html` file by opening the web console for the pop-up and checking `document.location.href`.
In my case this is `safari-web-extension://40C7D6FF-4D38-4A4C-A879-5ED2402182F4/popup.html`, however as we discussed, this guid (the `40C7D`...etc part, changes on each Safari restart.
If I type `safari-web-extension://40C7D6FF-4D38-4A4C-A879-5ED2402182F4/popup.html` into the browser's address bar, it will happily load it and show the BrowserAction page.
However if I try to load it within another webpage (e.g. as an iframe), I get an error message.
This is a security precaution; since the code running in the extension has elevated rights, you don't want a webpage to be able to take advantage of a badly coded extension.
A webpage would still be hard-pressed to find the guid of the extension, since it changes so often, but you could imagine that this guid would somehow leak during a run.
In our case however, we exactly *want* this behaviour: we want the webpage to open an iframe that we host in the extension (since it's the extension, specifically the ContentScript, creating the iframe, it has no problem finding out the guid of the extension using [`runtime.getURL()`](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/runtime/getURL)).
So in order to make the `applemap.html` (which is the page we show in the iframe) accessible from another webpage, we have to add it to `web_accessible_resources`.
Obviously MDN [also has a page describing `web_accessible_resources`](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/web_accessible_resources).

<details markdown="1">
<summary markdown="1" class="MD-inline">A BrowserAction (`popup.*`) page with some settings. You could manually set your home location, or use the browser's current location whenever showing a map.
</summary>

`popup.html`
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="popup.css">
</head>
<body>
    <h1>Show on map</h1>
    <img src="images/utrecht.png" id="utrecht">
    <p>
        This extension easily allows one to see a map of something on a webpage.
        Just right-click (or command-click, or two-finger-click) the word (or select multiple words and right click), and select "Show XXXX on a map".
        This should work for city names, addresses, and points of interest.
        Please see <a href="https://show-on-map.claude-apps.com" target="_blank">here</a> for more information, troubleshooting, the privacy statement and contact details of the author.
    </p>
    <hr>
    <h3>Settings</h3>
    <div>
        <h4>Home location&nbsp;&nbsp;<a href="https://show-on-map.claude-apps.com/settings.html#homelocation" target="_blank">&#9432;</a></h4>
        <select id="homeLocation">
        </select>
        <div id="longlat" class="hidden">
            <p>
                Please set your home location; use a tool like <a href="https://www.latlong.net" target="_blank">longlat.net</a> to determine your home location.
            </p>
            <div>Latitude: <input type="text" id="latitude"></div>
            <div>Longitude: <input type="text" id="longitude"></div>
            <a id="mapslink" target="_blank">See the current location on a map</a>
        </div>
    </div>
    <div>
        <h4>Initial map zoom level&nbsp;&nbsp;<a href="https://show-on-map.claude-apps.com/settings.html#zoomlevel" target="_blank">&#9432;</a></h4>
        <select id="showHomeLocation">
        </select>
    </div>
</body>
<script type="module" src="popup.js"></script>
</html>
```

`popup.css`
```css
:root {
    color-scheme: light dark;
}

body {
    width: 400px;
    padding: 10px;

    font-family: system-ui;
}

p, div {
    font-size: 0.8em;
}

a {
    text-decoration: none;
}

a, a:visited {
    color: #337FEE;
}

h4 {
    margin-top: 9px;
    margin-bottom: 2px;
}

#utrecht {
    position: absolute;
    top: 20px;
    right: 30px;
    width: 175px;
    height: 70px;
}


#longlat {
    overflow: hidden;
    transition: height 1s;
    height: auto;
}

#longlat.hidden {
    height: 0
}

input.error {
    color: red;
}


@media (prefers-color-scheme: dark) {
    /* Dark Mode styles go here. */
    a, a:visited {
        color: #55AFFF;
    }
}
```

`popup.ts`
```typescript
import {Settings, selectOptionsMap, SelectOptionsMapType} from "./shared.js"

const settings = await Settings.load()

function setupSelect<K extends keyof SelectOptionsMapType>(
  select: HTMLSelectElement,
  selectOptionsKey: K): void {
    console.log("start", select, settings, selectOptionsKey)
    const selectedValue = settings.selectSettings[selectOptionsKey]
    while (select.options.length) {
      select.options.remove(0)
    }

    Object.entries(selectOptionsMap[selectOptionsKey]).forEach(([key, value]) => {
      const option = document.createElement("option") as HTMLOptionElement;
      option.value = key
      option.innerText = value.name
      select.options.add(option)
    })
    select.value = selectedValue

    select.addEventListener("change", async () => {
      //@ts-ignore
      settings.selectSettings[selectOptionsKey] = select.value as keyof SelectOptionsMapType[K]
      await settings.save()
      updateLongLatVisibility()
    })
}

function updateLongLatLink() {
  ;(document.getElementById("mapslink") as HTMLAnchorElement).setAttribute(
    "href",
    `http://maps.apple.com/?q=${settings.homeLocation.latitude},${settings.homeLocation.longitude}`)
}

function updateLongLatVisibility()  {
  if (settings.selectSettings.homeLocation != "setLocation") {
    document.getElementById("longlat")!.classList.add("hidden");
  } else {
    document.getElementById("longlat")!.classList.remove("hidden");
  }
}

function setupLongLat() {
  const axes: ("latitude" | "longitude")[] = ["latitude", "longitude"]
  const range = {
    "latitude": 90,
    "longitude": 180,
  }
  axes.forEach((name) => {
    const element = (document.getElementById(name)! as HTMLInputElement)
    element.value = "" + settings.homeLocation[name]
    element.addEventListener("input", async (_event) => {
      const value = Number(element.value)
      if (Number.isNaN(value) || Math.abs(value) > range[name]) {
        element.classList.add("error")
        return
      }
      element.classList.remove("error")
      settings.homeLocation[name] = value
      await settings.save()
      updateLongLatLink()
    })
  })
  updateLongLatVisibility()
  updateLongLatLink()
}

setupSelect(document.getElementById("homeLocation") as HTMLSelectElement,
            "homeLocation")
setupSelect(document.getElementById("showHomeLocation") as HTMLSelectElement,
            "showHomeLocation")

setupLongLat()

export {}  // tells typescript that this is a module
```

`shared.ts`
```typescript
export type SelectOptions<K extends string, T> = {
  [key in K]-?: {
    name: string
    data: T
  }
}

export type ShowHomeLocationOpions = SelectOptions<"yes" | "no", boolean>;
export const SHOW_HOME_OPTIONS: ShowHomeLocationOpions = {
  "yes": {name: "Both home and found location", data: true},
  "no": {name: "Only found location", data: false},
}


export type InPageMapProviders = SelectOptions<"apple", {url: string}>
export const IN_PAGE_OPTIONS: InPageMapProviders = {
  "apple": {name: "Apple Maps", data: {url: "/applemap.html?search={search}"}}
}
type NewTabMapProviders = SelectOptions<"apple" | "google" | "bing" | "openstreetmap", {url: string}>

export const NEW_TAB_OPTIONS: NewTabMapProviders = {
  "apple": {name: "Apple Maps", data: {url: "/applemap.html"}},
  "google": {name: "Google Maps", data: {url: "/applemap.html"}},
  "bing": {name: "Bing Maps", data: {url: "/applemap.html"}},
  "openstreetmap": {name: "OpenStreetMap", data: {url: "/applemap.html"}},
}

export type HomeLocationTypes = SelectOptions<"useCurrentLocation" | "setLocation" | "noLocation", "useCurrentLocation" | "setLocation" | "noLocation">

export const HOME_LOCATION_OPTIONS: HomeLocationTypes = {
  "useCurrentLocation": {name: "Get \"current location\" when showing a map", data: "useCurrentLocation"},
  "setLocation": {name: "Use a fixed home location", data: "setLocation"},
  "noLocation": {name: "Don't use a home location", data: "noLocation"},
}

export type GeoLocation = {
  latitude: number
  longitude: number
}

export const selectOptionsMap = {
  inPageMapProvider: IN_PAGE_OPTIONS,
  newTabMapProvider: NEW_TAB_OPTIONS,
  homeLocation: HOME_LOCATION_OPTIONS,
  showHomeLocation: SHOW_HOME_OPTIONS,
}

export type SelectOptionsMapType = typeof selectOptionsMap

export type SelectSettings = {
  [key in keyof SelectOptionsMapType]: keyof (SelectOptionsMapType[key])
}

export class Settings {
  version: number
  selectSettings: SelectSettings
  homeLocation: GeoLocation

  constructor(version: number, selectSettings: SelectSettings, homeLocation: GeoLocation) {
    this.version = version
    this.selectSettings = selectSettings
    this.homeLocation = homeLocation
  }

  static getDefault(): Settings {
    return new Settings(1,
                        {inPageMapProvider: "apple",
                          newTabMapProvider: "apple",
                          homeLocation: "useCurrentLocation",
                          showHomeLocation: "yes"
                        },
                        {latitude: 49.843, longitude: 9.902056})

  }
  static async load(): Promise<Settings> {
    const settings = (await browser.storage.local.get("settings") as any)["settings"] as Settings | undefined
    if (!settings) {
      return Settings.getDefault()
    }
    return new Settings(
      settings.version,
      settings.selectSettings,
      settings.homeLocation
    )
  }

  async save() {
    await browser.storage.local.set({settings: {
      version: this.version,
      selectSettings: this.selectSettings,
      homeLocation: this.homeLocation,
    }})
  }

  getSelectSetting<K extends keyof SelectOptionsMapType>(name: K): SelectOptionsMapType[K][keyof SelectOptionsMapType[K]] {
    const options: SelectOptionsMapType[K] = selectOptionsMap[name]
    //@ts-ignore
    const key: keyof SelectOptionsMapType[K] = this.selectSettings[name]
    return options[key]
  }
}
```
</details>
It might be beneficial to quickly describe what's going on here.
Basically, this page shows 2 settings.
The first determine if you always want to show your current location on the map as well (which influences zooming).
The second is to set your home-location, where all searches should be done local to.

The second setting is quite irritating since as far as I know the BrowserAction did not have a way to retrieve the current location, so it actually directs you to a website to manually set your longitude and latitude.
This was a simple work-around, later revisions could have been smarter about this.

The `shared.ts` file simply defines some types and helper functions to deal with the settings.

<details markdown="1">
<summary>The background script</summary>

`background.ts`
```typescript
browser.menus.create({
  id: "open-in-maps-inpage",
  title: "Show map of '%s'",
  contexts: ["selection"],
  icons: {
    "16": "images/icon-16.png",
    "32": "images/icon-32.png",
  }
});

browser.menus.onClicked.addListener(async function(info, tab) {
  if (info.menuItemId == "open-in-maps-inpage") {
    if (info.selectionText) {
      const search = encodeURIComponent(info.selectionText);
      const url = browser.runtime.getURL(`/applemap.html#search=${search}`)
      if (!await browser.tabs.sendMessage(tab.id!, {"method": "ping"})) {
        console.log("installing contentscript")
        await browser.tabs.executeScript(tab.id!, {file: "/content.js"})
      }
      console.assert(
        !!await browser.tabs.sendMessage(tab.id!, {method: "showoverlay", url}))
    }
  }
});
```
</details>>

The background script gets loaded when the browser starts, and stays active until the browser is closed (since we chose `persistent: true` in the manifest).
It does 2 things: create a content menu item which is only shown if text is selected (note that right-clicking on a word always selects that word), with the text "Show map of XXXX", with XXXX being replaced by the selected text.
I add some icons to the context menu item, but at the time of writing, [icons are not supported in Safari](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/menus), so this code is not doing anything.

The second part is a listener for the menu item; it pings the ContentScript (with a `tabs.sendMessage()`) to see if it was already loaded; if not, it will load the ContentScript.
Once the script is loaded, a message is sent with the URL that should be opened in the iframe.


<details markdown="1">
<summary>The content script</summary>
`content.ts`
```typescript
type ShowOverlayMessage = {
  method: "showoverlay"
  url: string
}

const MINIMAL_WINDOW_SIZE = 300
const ARROW_BASE_LENGTH = 40

type Point = [number, number]
type BorderPoints = Point[]

function determineOverlayRect(): [DOMRect, BorderPoints] {
 const orientation: "portrait" | "landscape" = window.innerWidth > window.innerHeight ? "portrait" : "landscape"
  let width = Math.max(MINIMAL_WINDOW_SIZE, orientation === "landscape" ? window.innerWidth - 100 : window.innerWidth / 2 - 50);
  let height = Math.max(MINIMAL_WINDOW_SIZE, orientation === "portrait" ? window.innerHeight - 100 : window.innerHeight / 2 - 50);

  const selectionRect = window.getSelection()?.getRangeAt(0).getBoundingClientRect();
  if (!selectionRect) {
    return [new DOMRect(window.scrollX + 50, window.scrollY + 50, width, height), [
      [0, 0],
      [width, 0],
      [width, height],
      [0, height],
    ]]
  }
  const windowmid = [window.innerWidth / 2, window.innerHeight / 2];
  const selectionmid = [selectionRect.x + selectionRect.width / 2,
                        selectionRect.y + selectionRect.height / 2];
  if (orientation === "portrait") {
    const arrowstart = Math.min(
      Math.max(ARROW_BASE_LENGTH * 0.5,
               selectionmid[1] - ARROW_BASE_LENGTH * 0.5 - 50),
               height - ARROW_BASE_LENGTH * 1.5)
    if (windowmid[0] < selectionmid[0]) {
      const newwidth = Math.max(width, selectionRect.x - 50 - 50)
      return [new DOMRect(window.scrollX + 50, window.scrollY + 50, newwidth, height), [
        [0, 0],
        [newwidth, 0],
        [newwidth, arrowstart],
        [selectionRect.x - 5 - 50, selectionmid[1] - 50],
        [newwidth, arrowstart + ARROW_BASE_LENGTH],
        [newwidth, height],
        [0, height],
      ]]

    } else {
      const newwidth = Math.max(width, window.innerWidth - 50 - (selectionRect.x + selectionRect.width + 50))
      const windowX = window.scrollX + window.innerWidth - newwidth - 50
      return [
        new DOMRect(windowX, window.scrollY + 50, newwidth, height), [
          [0, 0],
          [newwidth, 0],
          [newwidth, height],
          [0, height],
          [0, arrowstart + ARROW_BASE_LENGTH],
          [selectionRect.x + selectionRect.width + 5 - windowX + window.scrollX, selectionmid[1] - 50],
          [0, arrowstart],
        ]]
    }
  } else {
    const arrowstart = Math.min(
      Math.max(ARROW_BASE_LENGTH * 0.5,
               selectionmid[0] - ARROW_BASE_LENGTH * 0.5 - 50),
      width - ARROW_BASE_LENGTH * 1.5)
    if (windowmid[1] < selectionmid[1]) {
      const newheight = Math.max(height, selectionRect.y - 50 - 50)
      return [new DOMRect(window.scrollX + 50, window.scrollY + 50, width, newheight), [
          [0, 0],
          [width, 0],
          [width, newheight],
          [arrowstart + ARROW_BASE_LENGTH, newheight],
          [selectionmid[0] - 50, selectionRect.y - 5 - 50],
          [arrowstart, newheight],
          [0, newheight],
        ]]
    } else {
      const newheight = Math.max(height, window.innerHeight - 50 - (selectionRect.y + selectionRect.height + 50))
      const windowY = window.scrollY + window.innerHeight - newheight - 50
      return [
        new DOMRect(window.scrollX + 50, windowY, width, newheight), [
          [0, 0],
          [arrowstart, 0],
          [selectionmid[0] - 50, selectionRect.y + selectionRect.height + 5 - windowY + window.scrollY],
          [arrowstart + ARROW_BASE_LENGTH, 0],
          [width, 0],
          [width, newheight],
          [0, newheight],
        ]]
    }
  }
}

let last_overlay: HTMLDivElement | null = null
async function showOverlay(url: string): Promise<void> {
  console.log("showOverlay", url)
  if (last_overlay) {
    last_overlay.remove()
  }
  const [position, borderPoints] = determineOverlayRect()

  const overlay = document.createElement("div")
  overlay.style.position = "absolute"
  overlay.style.top = position.top + "px";
  overlay.style.left = position.left + "px";
  overlay.style.width = position.width + "px";
  overlay.style.height = position.height + "px";
  overlay.style.zIndex = "100000";

  const [xs, ys] = [0, 1].map(i => borderPoints.map(point => point[i]))
  // make the SVG slightly larger than the coordinates so line width doesn't get clipped
  const [minX, maxX, minY, maxY] = [
    Math.min(...xs), Math.max(...xs),
    Math.min(...ys), Math.max(...ys)]
  const border = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  border.style.position = "absolute";
  border.style.left = minX + "px"
  border.style.top = minY + "px"
  border.setAttribute("width", (maxX - minX) + "px")
  border.setAttribute("height",( maxY - minY) + "px")
  border.setAttribute("viewBox", `${minX} ${minY} ${maxX - minX}, ${maxY - minY}`)

  const d = "M" + borderPoints.map(([x, y]) => x  + "," + y).join(" L") + "Z"
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs")
  const clipPath = document.createElementNS("http://www.w3.org/2000/svg", "clipPath")
  clipPath.setAttribute("id", "border_mask")
  const borderMask = document.createElementNS("http://www.w3.org/2000/svg", "path")
  borderMask.setAttribute("d", d)
  borderMask.style.fill = "black"
  borderMask.style.stroke = "none"
  clipPath.appendChild(borderMask)
  defs.appendChild(clipPath)
  border.appendChild(defs)

  const bgpath = document.createElementNS("http://www.w3.org/2000/svg", "path")
  bgpath.setAttribute("d", d)
  bgpath.style.fill = "#FFE"
  bgpath.style.stroke = "black"
  bgpath.style.strokeWidth = "10px"
  bgpath.style.strokeMiterlimit = "100"
  bgpath.setAttribute("clip-path", "url(#border_mask)")
  border.appendChild(bgpath)

  const fgpath = document.createElementNS("http://www.w3.org/2000/svg", "path")
  fgpath.setAttribute("d", d)
  fgpath.style.fill = "none"
  fgpath.style.stroke = "#FFE"
  fgpath.style.strokeWidth = "8px"
  fgpath.style.strokeMiterlimit = "100"
  fgpath.setAttribute("clip-path", "url(#border_mask)")
  border.appendChild(fgpath)

  overlay.appendChild(border)

  const iframe = document.createElement("iframe")
  iframe.setAttribute("width", (position.width - 10) + "px")
  iframe.setAttribute("height", (position.height - 10) + "px")
  iframe.setAttribute("src", url)
  iframe.setAttribute("allow", "geolocation")
  iframe.style.border="0";
  iframe.style.margin="5px";
  iframe.style.position="relative";
  overlay.appendChild(iframe);
  document.body.appendChild(overlay)

  const closeButton = document.createElement("button")
  closeButton.style.position = "absolute"
  closeButton.style.top = "4px"
  closeButton.style.right = "4px"
  closeButton.style.transform = "translate(50%, -50%)"
  closeButton.addEventListener("click", () => {
    overlay.remove();
    last_overlay = null;
  })
  closeButton.innerHTML = "&#x274C;"
  closeButton.style.backgroundColor = "#FFE"
  closeButton.style.padding = "5px"
  closeButton.style.textAlign = "center"
  closeButton.style.borderRadius = "50%"
  closeButton.style.border = "1px solid black"
  closeButton.style.width = "30px";
  closeButton.style.height = "30px";
  closeButton.style.fontSize = "10px";
  overlay.appendChild(closeButton);

  last_overlay = overlay;
}

browser.runtime.onMessage.addListener((message: any, _sender: any, sendResponse: (message: any) => any): void  => {
  switch (message.method) {
    case "showoverlay":
      message = message as ShowOverlayMessage
      showOverlay(message.url)
      sendResponse(true)
      break
    case "ping":
      sendResponse(true)
      break
    default:
      console.error("Don't know what to do with message", {message})
      sendResponse(false)
  }
})
```
</details>
It should be noted that the largest part of the ContentScript deals with drawing a nice overlay, moving it to a spot so that it doesn't occlude the selected words, draw a nice arrow to the selected words, and finally creating an iframe based on the message it received from the BackgroundScript.

<details markdown="1">
<summary>The content of the iframe</summary>
`applemap.html`
```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">

<style>
html, body, #map {
    width: 100%;
    height: 100%;
    box-sizing: border-box;
    margin: 0;
    overflow: hidden;
}

#map {
}
</style>

</head>

<body>
<iframe id="map" width="100%" height="100%" scrolling="no" allow="geolocation"></iframe>

<script src="applemap.js" type="module"></script>
</body>
</html>
```

`applemap.ts`
```typescript
import {Settings} from "./shared.js"

const url = "https://show-on-map.claude-apps.com/applemap.html" + document.location.search + document.location.hash
const iframe = document.getElementById("map")! as HTMLIFrameElement
iframe.setAttribute("src", url)
iframe.style.border="0";

window.onmessage = async (event) => {
  if (event.origin != "https://show-on-map.claude-apps.com") {
    return
  }
  const settings = await Settings.load()
  const homeLocationSetting = settings.getSelectSetting("homeLocation").data 
  iframe.contentWindow!.postMessage({
    useCurrentLocation: homeLocationSetting == "useCurrentLocation",
    homeLatitude: homeLocationSetting == "noLocation" ? null : settings.homeLocation.latitude,
    homeLongitude: homeLocationSetting == "noLocation" ? null : settings.homeLocation.longitude,
    showHomeLocation: settings.getSelectSetting("showHomeLocation").data,
  } , "https://show-on-map.claude-apps.com/");
}
```

`shared.ts` source code can be found above in the BrowserAction section.
</details>

Nothing special here, within the iframe we just create another iframe tag (now not limited by the CSP settings of the parent page) where we show `https://show-on-map.claude-apps.com/applemap.html?....#.....`.
This latter page will contain the map.
Note that the search is actually contained in the hash (the part after the `#` in the URL) so that it will not appear in any web server logs.

It will then wait for a message from this iframe, and when it receives one it will send the settings.

I have to admit that it's a bit weird to send one piece of info (the search term) through the hash, and another piece through the messaging system; this was a version 0.5, and probably I would have chosen one or the other for a final version.

<details markdown="1">
<summary>Finally, the code hosted on show-on-map.claude-apps.com</summary>
`applemap.html` (note that this is a different file from `applemap.html` that is part of the extension)
```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">

<script src="https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.js"></script>

<style>
html, body {
    width: 100%;
    height: 80%;
    overflow: hidden;
}

#map {
    width: calc(100% - 2px);
    height: calc(100% - 30px);
    position: absolute;
    top: 30px;
    left: 1px;
}
body {
    background-color: #FFE;
    margin: 0;
}
#message {
    background-color: #EEC;
    padding: 15px;
    margin: 2px;
    border: 2px solid #332;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%,-50%);
    opacity: 1;
    transition: opacity 1s;
}
#message.hidden {
    opacity: 0;
}

h1 {
    margin: 2px;
    font-size: 22px;
}

a {
    color: black;
    font-size: 0.8em;
}
a:visited {
    color: black;
}

a#help {
    position: absolute;
    bottom: calc(100% - 1.2em);
    right: 10em;
}

a#openinmaps {
    position: absolute;
    bottom: calc(100% - 1.2em);
    right: 2em;
}
</style>

</head>

<body>
<h1>Show on map Safari Extension</h1>
<a id="help" href="https://show-on-map.claude-apps.com/" target="_blank">about &amp; help</a>
<a id="openinmaps"></a>
<div id="map" data-token-id="eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjY3RDZBV0E1Tk4ifQ.eyJpc3MiOiI5VFA1WVE4WlVDIiwiaWF0IjoxNjM1MTA2Mjg0LCJleHAiOjE2NjY1Njk2MDAsIm9yaWdpbiI6Imh0dHBzOi8vc2hvdy1vbi1tYXAuY2xhdWRlLWFwcHMuY29tIn0.Nypg_NDhqPmvpGpem1UNd7sXrcqYj1Vjngk6JsDBo47QqfkLnfuM9yve7exCyBdiXButQ6OjBc8Ps8KtLHmy8w"></div>

<div id="message">Loading map...</div>

<script src="applemap.js"></script>
</body>
</html>
```

`applemap.ts` (again, not the same as its namesake in the extension)
```typescript
const tokenID = document.getElementById("map")!.getAttribute("data-token-id")!

function showMap(homeLatitude: number | null, homeLongitude: number | null, showHomeLocation: boolean) {
  mapkit.init({
      authorizationCallback: function(done) {
          done(tokenID);
      }
  });
  const homeLocation = homeLatitude === null || homeLongitude === null ? null : new mapkit.Coordinate(homeLatitude, homeLongitude);
  const searchTerm = (new URLSearchParams(document.location.hash.slice(1))).get("search");
  if (!searchTerm) {
    document.getElementById("message")!.innerText = "Error: No search term."
  } else {
    document.getElementById("openinmaps")!.innerHTML = "Open in Maps &#8599;"
    document.getElementById("openinmaps")!.setAttribute("href", "http://maps.apple.com/?q=" + encodeURIComponent(searchTerm))
    document.getElementById("openinmaps")!.setAttribute("target", "_blank")
    document.getElementById("message")!.innerText = "Looking for \"" + searchTerm + "\"...";
    const region = homeLocation === null ? undefined : new mapkit.CoordinateRegion(homeLocation, new mapkit.CoordinateSpan(0.1, 0.1));
    (new mapkit.Search({region: region})).search(searchTerm, (error, data) => {
      if (error) {
        document.getElementById("message")!.innerText = "Error occured: " + error
        return
      }
      console.log(data)
      if (data.places.length == 0) {
        document.getElementById("message")!.innerText = `No search results for '${searchTerm}'.`
        return
      }
    const homeMarker = homeLocation === null ? null : new mapkit.MarkerAnnotation(
      homeLocation, {
        color: "blue",
        title: "Home",
        titleVisibility: mapkit.FeatureVisibility.Visible})
    document.getElementById("message")!.innerText = "Found \"" + searchTerm + "\", loading map...";
      const map = new mapkit.Map(
        document.getElementById("map")!,
        {
          annotations: [
            ...data.places.map(
              (place) => new mapkit.MarkerAnnotation(
                place.coordinate, {
                  title: place.name,
                  titleVisibility: mapkit.FeatureVisibility.Visible})),
            ...showHomeLocation && homeMarker ? [homeMarker] : [],
            ],
          //@ts-ignore
          region: showHomeLocation ? undefined : data.boundingRegion,
        }
      )
      window.setTimeout(() => {
        document.getElementById("message")!.classList.add("hidden")
        if (!showHomeLocation && homeMarker) {
          // add home marker now; map will already have zoomed to found markers
          map.addAnnotation(homeMarker)
        }
      }, 500);
    }, );
  }
}

var getPosition = function (options: Parameters<typeof navigator.geolocation.getCurrentPosition>[2]) : Promise<Parameters<Parameters<typeof navigator.geolocation.getCurrentPosition>[0]>[0]> {
  return new Promise(function (resolve, reject) {
    navigator.geolocation.getCurrentPosition(resolve, reject, options);
  });
}

window.onmessage = async (event) => {
  if (event.origin.startsWith("safari-web-extension://")) {
    let homeLatitude: number | null
    let homeLongitude: number | null
    console.log({event})
    if (event.data.useCurrentLocation) {
      let currentCoordinates = (await getPosition({maximumAge: 900})).coords
      homeLatitude = currentCoordinates.latitude
      homeLongitude = currentCoordinates.longitude
    } else {
      homeLatitude = event.data.homeLatitude as number | null
      homeLongitude = event.data.homeLongitude as number | null
    }
    const showHomeLocation = event.data.showHomeLocation as boolean
    showMap(homeLatitude, homeLongitude, showHomeLocation)
  }
}
window.parent.postMessage("loaded", "*")
```
</details>>

These files are the ones doing the actual work interacting with MapKit JS and creating the map (you will have to replace the MapKit key with your own if you want to play with this).
It talks to the parent iframe, gets the settings, retrieves the current location if necessary, converts the search text into geolocations and then shows the map.
If we want the map to show both the home and found locations, we add Home as a marker on the map upon creation, else we add the home marker half a second after creating the map (assuming that by then the map decided its zoom level and will not need anything else).

You can also see the work around I discussed earlier creating a `mapkit.CoordinateRegion` of 0.1 degree around the point we're interested in.


## Version 1.0
As I mentioned before I was never quite happy with the multiple layers of iframes needed for v0.5, nor with the fact that what I thought should be nice self-contained extension all of a sudden needed an external component (the code on `show-on-map.claude-apps.com`).
However I submitted v0.5 for approval, thinking that I could always look into it in more detail later if I wanted (Apple allows you to submit an app for app store approval without actually releasing it; so I could submit this, see how Apple reacted, and possibly later clean up the code before I made an app store release).

Apple rejected v0.5, they said it didn't work for them on the newest Safari.
It was developed on that same version, so I still don't know what went wrong; I did feel however that too many moving parts (a BackgroundScript that opens and sends messages to a ContentScript, which then opens an iframe with a script which opens another iframe, after which the iframes talk to each other as well) would be very hard to debug if users would start to complain.
So version 1.0 would throw away all that work done for 0.5, and start again.

<figure class="half">
    <img src="/assets/images/2021/12/05/mark-twain-example-v1.jpg">
    <img src="/assets/images/2021/12/05/giza-example-v1.jpg">
    <figcaption>Showing v1 in action, finding Mark Twain (again) and the Pyramids in Giza</figcaption>
</figure>

Version 1.0 takes a wholly other approach: there are no settings (somehow I've been unable to make the BrowserAction disappear altogether; it just shows a static HTML page now with a few instructions), and when the menu-item is selected the search-term is sent to the Apple Maps app (which, as far as I know, is installed on every mac).

Opening the Apple Maps app is easy, since as soon as Safari opens a link to maps.apple.com, it will forward it to apple maps (see <a href="http://maps.apple.com/?q=Haarlem,Netherlands" target="_blank">this example</a>).
However (as I'm sure you've noticed if you actually clicked the link above), it asks user confirmation to open the Maps app, and it leaves open the tab used for the link.

So in order to fix this problem, I have the native part of the extension (go back to the top if you forgot by now what this is) open the Maps app, and voila, it fixes both problems!
It did take me a long long time to get the communication between the native part of the extension and the HTML/JS part working (which I'm sure is due to my inexperience in Xcode and mac development), but once it works, it couldn't be easier!

<details markdown="1">
<summary>The native part of the extension: SafariWebExtensionHandler.swift</summary>
`SafariWebExtensionHandler.swift`
```swift

import SafariServices


let SFExtensionMessageKey = "message"

class SafariWebExtensionHandler: NSObject, NSExtensionRequestHandling {

    func beginRequest(with context: NSExtensionContext) {
        let item = context.inputItems[0] as! NSExtensionItem
        let message = item.userInfo?[SFExtensionMessageKey]

        if let dictMsg = message as? NSDictionary, let openURL = dictMsg["openURL"] as? String {
            NSWorkspace.shared.open(URL(string: openURL)!)

            let response = NSExtensionItem()
            response.userInfo = [ SFExtensionMessageKey: "Opened url " + openURL ]
            context.completeRequest(returningItems: [response], completionHandler: nil)
        } else {
            let response = NSExtensionItem()
            response.userInfo = [ SFExtensionMessageKey: ["error": "don't understand message", "message": message ]]
            context.completeRequest(returningItems: [response], completionHandler: nil)
        }
    }
}
```
</details>

The above file (Swift 5) is all the code necessary for the native part.
Let me go through it:
The function `func beginRequest(with context: NSExtensionContext)` is the function that receives the calls from the HTML/JS part (which uses `browser.runtime.sendNativeMessage` to send these messages) -- note that you need the `nativeMessaging` permission in the manifest for this to work at all.
You will need the `context.inputItems[0].userInfo[SFExtensionMessageKey]` to get to the message -- not entirely sure what the rest of the context contains.

The rest of the code is pretty straight forward: I check that the message is a dict and that it has a key `openURL` which is a string.
If so, call `NSWorkspace.shared.open(URL(string: openURL)!)`, which tells the system to open the URL.
Then I send back a success message to the HTML/JS part of the extension.

The code above has no limits on what URLs can be opened, however since the native extension can only receive messages from the HTML/JS part of the same extension (not of other extensions, or (worse) webpages you visit, there is no real risk (although because of defence in layers it is better to validate the URL).

The thing that made developing the native part of the extension really hard, is that I couldn't find a hook to find out what was going on in that file.
When you start the extension in Xcode, the debugger connects to the native application (not the native part of the extension!) -- probably someone better at Xcode than me could fix this, but not me.
I was using `os_log` to log messages to the system log (`import os.log`; `os_log(.default, "Received message from browser.runtime.sendNativeMessage: %@", message as! CVarArg)`), however there is a protection in `os_log` which means that variables are reported as `<private>` in the logs (it took me hours to find out that the variable wasn't private (as in: private fields in an object), but the logger though the data might be private....). The solution (once you know it) is to use `os_log(.default, "Received message from browser.runtime.sendNativeMessage: %{public}@", message as! CVarArg)`.
It's still a shit way to develop (print statements and running....) but it's much much better than blind development.

BTW, once you know where to look..... [This stack-overflow reply](https://stackoverflow.com/a/45957891/1207489) has all the answers.


<details markdown="1">
<summary>The BackgroundScript</summary>
`background.ts`
```typescript
import { init, track, parameters} from "insights-js"
init("WtawK18B7KdIwM9X")


browser.menus.create({
  id: "open-in-maps-inpage",
  title: "Show '%s' on a map",
  contexts: ["selection"],
  icons: {
    "16": "images/icon-16.png",
    "32": "images/icon-32.png",
  }
});

browser.menus.onClicked.addListener(async function(info, _tab) {
  if (info.menuItemId == "open-in-maps-inpage") {
    if (info.selectionText) {
      const search = encodeURIComponent(info.selectionText);
      const url = `http://maps.apple.com/?q=${search}`
      //@ts-ignore
      browser.runtime.sendNativeMessage("application.id", {openURL: url}, (response: object) => {
        if (response as String === "Opened url " + url) {
          track({id: "extension-used", parameters: { result: "success", locale: parameters.locale()} } )
        } else {
          track({id: "extension-used", parameters: { result: "fail", locale: parameters.locale()} } )
        }
        console.log("response from native app: ", response);
      })
    }
  }
});

```

`background.html`
```html
<!DOCTYPE html>
<!-- page is just here so that background.js will be loaded as module -->
<html>
<head>
    <meta charset="UTF-8" />
    <script type="module" src="background.js"></script>
</head>
</html>
```
</details>

All the BackgroundScript does is set up the context menu item and once it's clicked, create a URL of the form `http://maps.apple.com/?q=XXXX` and send a message to the native part of the extension to open this URL (note: as far as I have been able to determine, all connections are secure, even though an `http://` URL is used; Apple Maps will intercept the URL and use secure connections to get the data).

Finally I send a ping to my tracking system so that I can know how much the extension is being used, and whether there was an error.

<div class="notice" markdown="1">
In my first extension I did not build any tracking, because I believe the web should be free (as in speech) and people should not be tracked.
The result was that after a couple of months I had quite some downloads, but no idea if people are actually using the extension, which makes it hard for me to decide if I should spend time on updates.
When I moved this blog from Medium to GitHub, I wanted some way of tracking use (because of the same reason; I'm more excited to write blog posts if I know people are reading them :)).
However I really don't want to make more money for Google or Facebook by helping them track people better (in addition to probably lots of people blocking these trackers anyways), so I looked for a tool that would track and use the data for nothing else than to let me know the stats.
In addition, I didn't want to start paying &euro;10 a month if only 5 people visited my blog.
I ended up selecting [`https://getinsights.io/`](https://getinsights.io/); they seem to share my values about privacy and not tracking people (just counting them; I want to *track* use by *counting* people, or events).
Anyways, so far I'm getting useful data from them, even though I sometimes wish for more graphs and visualisations; but I can have 3000 events for free a month, and I will not complain!

I have to say that I'm still struggling with the ethics of releasing an update of the other extension which counts use; I feel I betray those people that installed the extension after reading the promise that I was not tracking them (and not reading through all the changes at an app update, as none of us do).
</div>

<details markdown="1">
<summary>Finally, the manifest</summary>
`manifest.json`
```json
{
    "manifest_version": 2,
    "default_locale": "en",

    "name": "__MSG_extension_name__",
    "description": "__MSG_extension_description__",
    "version": "1.0",

    "icons": {
        "48": "images/icon-48.png",
        "96": "images/icon-96.png",
        "128": "images/icon-128.png",
        "256": "images/icon-256.png",
        "512": "images/icon-512.png"
    },

    "background": {
        "page": "background.html",
        "persistent": true
    },

    "browser_action": {
        "default_popup": "popup.html",
        "default_icon": {
            "16": "images/toolbar-icon-16.png",
            "19": "images/toolbar-icon-19.png",
            "32": "images/toolbar-icon-32.png",
            "38": "images/toolbar-icon-38.png"
        }
    },

    "permissions": [
        "menus",
        "activeTab",
        "nativeMessaging"
    ]
}
```
</details>
Note that we still need the `activeTab` permission.
I do think that this is unfortunate, since it means that the user sees the following warning.

{%include figure
    image_path="/assets/images/2021/12/05/warning.png"
    alt="Warning shown on the extensions screen"
    caption="Warning shown on the Safari Settings &gt; extensions screen. (yes I know the other extensions are blurred-but-still-readable; I think they're good extensions (especially Smart Keyword Search &#x1F600;), so I have to problem with showing them)"
%}

The Extensions page in the Safari Settings explains that this extension "[c]an read and alter sensitive information on web pages, including passwords, phone numbers and credit cards, and see your browsing history **on the current tab's web page when you use the extension.**".
This is absolutely correct, and I think these kinds of warnings can not be shown enough, however I would love to have a way to show that the extension never wants access to anything except the selected text when the menu item is clicked....

In addition obviously the `nativeMessaging` permission is necessary, and the `menu` permission.

For the background I specify a `page` rather than a `script`.
I don't think the `background.html` can display anything, however it [does allow](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Anatomy_of_a_WebExtension#specifying_background_scripts) me to load the `background.js` as an ES6 module, which means I can use things like `import` and top level `await` statements in `background.js`, which I use to import the `getinsights.io` JavaScript library.

### Wrapping up
In order to release the app on the App Store, you need to create an icon (which I tend to do in SVG and then scale to different sizes of PNGs before dragging them into Xcode), and add a static html file to show in the BrowserAction.
Some more housekeeping (replace the placeholder names and icons in the scaffold made by Xcode) and submit to Apple!
It was accepted within days, and live on the app store every since.

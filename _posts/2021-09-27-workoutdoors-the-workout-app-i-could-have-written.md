---
title: 'WorkOutDoors: The workout app I would have written for myself'
categories:
    - review
tags:
    - apple watch
    - workouts

header:
    image: /assets/images/2021/09/27/running.jpg
---

Ever since I got my first Apple Watch, I looked for apps to track workouts.
In the beginning, any app would do.
The most important thing was to give me feedback on how my workout was going; all the actual work was being done on the iPhone.
Over time however two things changed.

First, I started to get more serious about my workouts; I would run the occasional 10k, or half marathon, and wanted to do training for this.
This meant more complex workouts: intervals training, runs in hilly terrain, etc.

The second change is that these days an Apple Watch by itself is all you need on your runs.
Since a couple of years the Apple Watch has a GPS receiver, enough battery to track even the longest workouts (fair enough, during 12+ hours cycle tours I tend to charge my watch halfway) and storage so that you can take all the music / podcasts / audio books you need.
So about a year ago, I dropped the (bulky, never quite comfortable) iPhone from all my running workouts, and only use the Apple Watch.
Time to update the apps I'm using.

------

I used to use iSmoothRun as the running app of choice, back in the days when Apple Watches were nothing more but a annually returning rumour.
I settled on it after trying a couple of apps (RunGap, Nike), and liked it very much for many years.
However I did note that after I started wearing an Apple Watch, I tended to use the built-in Workouts app more and more; the iSmoothRun app for Watch had problems with stability (not nice if 10k into your half marathon, your watch decides to freeze and loose the whole workout), and I feel the app never quite reached the level on the Watch that it had on the phone.

<div class="notice" markdown="1">
As a quick side note: the apps I discuss here cost money.
When I look around me, I see many friends that really have a problem with paying for apps; they happily buy €150 running shoes, a €30 water belt that they'll never wear and €100 in gels and running snacks.
Without flinching they will buy a €3 bottle of water during their run (even though 200m further there is a free water fountain), but as soon as you suggest they pay €10 on a running app, they call you crazy.

There is a saying that there is no such thing as a free lunch; this is not completely true; open source software, and sites like Wikipedia, show that there is such a thing; and even on the app store there are multiple projects that are offered for free, just because the author enjoys if other people use what they made (hey, I have a [free Safari Extension on the App Store](https://sks.claude-apps.com/) myself).
However we see more apps these days that are "free" (between quotes).
They generally come with privacy statements that nobody ever reads (meaning: you probably agree for them to use your data), or there are in-app purchases needed to unlock anything but the basic functionality.

I *like* apps that ask for a (reasonably small) payment.
I understand them, I understand where they make their money, and I feel we join into a mutual agreement; I pay, they make sure the app keeps working (for a reasonable amount of time).

The apps I discuss in this article, both iSmoothRun and WorkOutDoors, cost less than €10 each; completely negligible compared to the other stuff I buy for my sports (and just to be clear: I advise buying only the latter one).
</div>

At some point I started to think about what my ideal workout app would look like (maybe with somewhere in the back of my mind that I could build it one day, if necessary):
- Obviously stability: nothing so frustrating as losing your progress halfway your run.
- Privacy: my running data is mine; I want to be able to share it with whom I want, and nobody else.
- Automatic syncing with Apple Watch Workouts (so that I still get my awards :))
- Runs on the Watch, but can also use the phone to run (for many sports, such as cycling and supping, I still have my phone with me).
- Flexible (and easy) creation of workouts with intervals.
- Customizable audio cues on my headphones (let me decide if I want a list of 20 metrics read out to me every km, or just a vibration on the watch, so I can check the metrics on my watch).
- Customization of metrics: when cycling in Netherlands, I don't want to give up precious screen real-estate on my watch on meters ascended/descended; however when I take my bike for a ride in the alps, I definitely want this data!
- Support for my workouts: running, walking, hiking, cycling, supping, wind-surfing and swimming.

After a run around a lake in Germany, where I ended up climbing over fences, going through fields and jumping over ditches after because I lost my way (Apple Maps only work when you have internet connection), I added one extremely important feature:
- Support for maps that get cached on the Watch.

<div class="notice" markdown="1">
Supposedly this year Apple will (finally) launch a 4G version of the Apple Watch that works in The Netherlands.
In theory this should mean that the Apple Maps *will* work when running without your phone.
There are however pitfalls.
We will have to see if the internet connectivity will work abroad (where chances of getting lost are highest); and even then, you may end up in an area without 4G coverage (again, higher chance of getting lost in these kinds of areas).
</div>

# WorkOutDoors

Ever since I found [WorkOutDoors](http://www.workoutdoors.net), I cannot stop singing the praises of this app.
It does *exactly* what I want from a workout app, stable, endless customisation, and it caches OpenStreetMap maps (in many areas [I have found OpenStreetMap to be more accurate](./2020-12-01-cycling-in-wroclaw.md#dont-trust-google-maps) than Google/Apple maps).
All customisation happens on the phone (where you have a bigger screen to configure everything), and settings are then sent to the Watch.
You define multiple screens for each workout type, and can easily switch between them on the watch.
For instance, when running I have a screen with a large map, and small metrics (for when I run in an unknown area), a screen with large metrics (for when I'm killing myself in a run and cannot focus on small writing), and a screen with interval information (for the interval runs).

{%include figure
    image_path="/assets/images/2021/09/27/WatchStripOverview.png"
    alt=""
    caption="Example screenshots from the [WorkOutDoors homepage](http://www.workoutdoors.net)"
%}

I have to admit that over the first couple of weeks I sometimes struggled with the sheer amount of items that could be configured.
The app has very reasonable defaults, but if you're anything like me, over the first workouts you constantly run into small and large things you like to adjust, meaning you are spending a couple of minutes after each workout tweaking your settings.
Once you have everything setup the way you want, you never want to go back though.

I have used it for pretty much everything I do: going for a run while on vacation, going supping in an area I'd never been before, or hiking through the alps.

Rather than listing all the amazing features, I advice you to take a look at the [app's homepage](http://www.workoutdoors.net).

<figure class="align-left half" style="width: 400px; margin-top: 7px;">
    <img src="/assets/images/2021/09/27/route.png">
    <img src="/assets/images/2021/09/27/route-zoom.png">
    <figcaption>Showing part of the route (zoomed out and zoomed in); note that I choose a light colour-scheme for the maps (talk about customization!). Normally you would see a blue arrow where you are, but I (obviously) forgot to take the screenshots when I was actually there....</figcaption>
</figure>
One of the (many) things that jump out for me is the ability to import GPX tracks as routes (and getting alerts if you go off route).
This allows you to easily import a track (someone else's workout downloaded from a webpage, a defined track, or a track you just clicked together in something like [Gaia](https://apps.apple.com/us/app/gaia-gps-hiking-offroad-maps/id1201979492)), and see it overlayed on the map.
You get alerts (visual, audible, haptic, you choose) when you go off track.
I have used this to import a [480km cycle track from Maastrict to Rotterdam](https://www.lfmaasroute.nl), and follow it over a couple of days, getting alerted if I missed a turn, and easily finding back the shortest path to the route after a detour.

<div style="clear: both"></div>

⭐️⭐️⭐️⭐️⭐️ The app has a 4.8 star rating in the app store (at time of writing), and costs less than a large coffee.

I'm not saying that the app is perfect, and completely without problems or bugs.
During my first weeks of use I ran into a number of small problems, and I sent off an email to the developer.
He replied to me within hours with detailed instructions on how to fix things (most of the problems were my own fault for not carefully reading the instructions), and promised to pick up the couple of minor bugs that I found in the next release.
Even the third or fourth time that I reached out, I got replies within hours (try that with a big company!).

If I had written a workout app for my own personal use, with all the features I wanted for myself, I would have come up with a small subset of what this app does (and then probably never finish implementing it, let's be honest :)).
For the use that I'm getting from it, €5.99 is laughably little for this app; if the author would have any "donate" button anywhere on the site, I would be more than happy to buy him a beer or two!
I guess that all I can do, is spread the word!

<div class="notice" markdown="1">
I want to be clear that I'm in no way involved with WorkOutDoors.
I'm in no way being paid to publish anything about them, nor will I get any kick-back if people buy the app.
I just think it's an amazing app, I would like to spread the word so that more people get to enjoy it.
And, being a independent software developer myself, I absolutely love when someone appreciates my work, and I'm more than happy to show others that I appreciate theirs!
</div>

---
title: "Hugo: Recurring events with iCalendar support"
categories:
    - how-to
tags:
    - hugo
toc: true
header:
    image: /assets/images/2022/12/11/header.jpg
    teaser: /assets/images/2022/12/11/teaser.jpg
---


## A recurring event
In the [Hacker Space Trójmiasto](https://hs3.pl), which I a visit when I'm in town, there are regular events.
We were looking for a way to put these events on the ([Hugo](https://gohugo.io)) website.
This is easy enough for simple events that happen occasionally (just hard-code the dates), but we had some extra requirements (two for the end-user, and two technical requirements):
- An easy way to define recurring meetings (like the monthly picnic, or the bi-weekly board-meeting).
- Ideally the members could download the event-data in [iCalendar](https://icalendar.org) (`.ics`) format.
- Of course you don't want to involve a programmer every time that an event gets changed (e.g. an organiser may want to cancel an event last-minute), so whatever format we use, needs to be readable (and editable) by humans :)
- Ideally everything will work "in-Hugo", so without an extra pre-compiler step, or something else.


Just to make clear what I'm talking about here.
There is a *section* "events", which contains *pages* (in Hugo terms).
A *page* is for a named "event-type" (like "picnic"), not a single event (like "picnic on 5 December 2022").
So a single *page* is for multiple dates.
On this page we want to show all the dates for the event, and allow someone to download these dates as an iCalendar (`.ics`) file.
To give you an idea of the structure, visit [the events-list here](https://hs3.pl/en/events/).
Note that, depending on when you're reading this, the system as described in this post may not be live yet.

Obviously on the `/events` list page we also have a calendar of all events (so the dates for all event-types together), with the same iCalendar support, as well as on the `tags`-pages, but this is outside the scope of this post.
{: .notice}
{% include figure
    image_path="/assets/images/2022/12/11/events.png"
    alt="Example of events on hugo page"
    caption="Demo of an event page (note that most dates here are for demo purposes only ;))"
%}

Above you see what we want to display at the top of an event-page (note: for real-life use you probably want to limit which part of the list you show, make it scrollable, choose a different format or colours, etc).
Final makeup is independent of the code generating the events (and so 100% custom).

When it comes to displaying the events on your webpage in a user-friendly way, you have to keep in mind that Hugo is a *static* site generator. It means that whenever in your Hugo code, you refer to `time.now`, this is the *generation time* of the website, not when the user will view it.
As a result you should never filter the events by "future events only" or "next 3 events" within Hugo (unless you regenerate your site every day or every hour or something); always write all events to the HTML, and then  create some javascript to show exactly what you want.
{: .notice--warning}

## Existing standards we considered
The first thing we did was define the format in which we would create the event-dates.
We need to be able to specify a rule (like: every last Friday of the month), but also allow for changes on this rule, one-off events, extra meetings, etc.
We would define this in the front-matter, and then show it in the page where we wanted.

Let's start by checking what's out there:

### OpenStreetMap OpeningHours
We first considered the [OpenStreetMap OpeningHours format](https://wiki.openstreetmap.org/wiki/Key:opening_hours).
It's super powerful and versatile; you can specify crazy rules like "Every other year the third day after Easter, from sunrise to sunset, except if this is a Sunday or a public holiday in your current country".
A big problem with this format is, however, that the only parser I know is the OpenStreetMap parser, which is written in JavaScript (in a previous life I once wrote a parser for Python, but it was far from complete (and not open-source)).
When writing your own parser, you would have to make a decision on what part of the syntax to support (you *could* probably write a spec compliant parser in Go Templates, but you don't really want to); and this means that you miss out on the powerful-ness of the language.
Looking at the example below, you can see that the format may be hard to read and maintain by a non-expert.
Considering all this, we dropped this idea.

<figure markdown="1">
```yaml
opening_hours: >
    Fr[-1] 18:00-24:00;
    2022 Sep Fr[-1] 18-24 "@ Noc Nauka Hevelianum";
    2022 Dec Fr[-1] 18-02 "Bring 🍾";
    2023 Jan Fr[-1] off;
    2023 Jan Sa[-1] 18-24 "On Saturday for once"
```
<figcaption markdown="1">
Example of how rules and exceptions look in OpenStreetMap OpeningHours
</figcaption>
</figure>


### iCalendar format
A second option we looked at, was the iCalendar (RFC 5545) [RRule format](https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html).
A quick look at the examples on that page, also shows why this format fails the "human readability" test (which meant that we didn't even spend time to check it against the other requirements).

<figure markdown="1">
```
DTSTART;TZID=America/New_York:19970902T090000
RRULE:FREQ=WEEKLY;INTERVAL=2;WKST=SU
```
<figcaption markdown="1">
Example of an iCalendar Recurring Event Rule. The format was never meant to be human-readable, and indeed, it isn't.
</figcaption>
</figure>

## Our own format
Finally we settled for our own format, and just see how far we would get with implementing this into Pure Hugo (=Go Templates).

<figure markdown="1">
```yaml
eventDates:
    periodics:
    - start: 2022-10-01
      end: 2023-09-01
      rule: last Friday of the month
      starttime: 18:00
      endtime: 02:00
    cancelled:
      2023-02-24: "Too cold"
      2023-07-28: vacation
    extra:
      2022-12-07 18:00-19:00: extra meeting too
      2023-08-27 18:00-19:00: extra meeting
      2022-10-29 18:00-05:00: DLS change party!
    changes:
      2022-10-28->2022-10-27: "moved because of planning issues"
      2022-12-30: bring 🍾
      2023-04-28->19:00-01:00: "starting a bit later"
      2023-06-30->2023-06-29 19:00-21:00: moved a day earlier
```
<figcaption markdown="1">
Our custom recurring event format.
</figcaption>
</figure>

The format we've chosen is a simple dictionary with 4 keys, all optional.
- `periodics`: a list of 0 or more rules to generate events. It has 4 required keys, and one optional one:
  - `start`: The first date that this rule should apply (NB: this does not mean that on this date an event happens, just that the rule will only be applied to dates that are larger-or-equal to this date.
  - `end`: The first date that this rule is *not* active anymore (so the day before this date is the last possible date for this rule.
  - `rule`: For now two rules are supported:
    - `every X days` where `X` is a number. In this case the first event is on the `start` date, and then once every `X` days, until the `end` date.
    - `ORDINAL WEEKDAY of the month`, where ORDINAL is one of (`first`, `second`, `third`, `fourth`, `fifth`, `last`, `penultimate`), and `WEEKDAY` is the name of a day of the week in English. So for example, this would lead to `last Friday of the month`
    - (At the moment it's not implemented, but it would be easy to make something like `every Xth of the month`, to allow events recurring on a certain date. More complex rules would probably also work)
  - `starttime`: Time the event starts (as 24h format)
  - `endtime`: Time the event ends (as 24h format). Note that if `endtime < starttime`, the event is expected to end the next day. Events lasting more than 24 hours are not supported for now.
  - `comment`: Optional field; a comment for each event of this rule.
- `cancelled`: Events that are cancelled, with a comment.
- `extra events`: extra (one-off) events, with start- and end-time and comment
- `changes`: This field allows for 4 different formats for keys (the values are always comments):
    - `YYYY-MM-DD`: Allows setting a comment on an existing event
    - `YYYY-MM-DD->YYYY-MM-DD`: Move an event from one date to another
    - `YYYY-MM-DD->HH:MM-HH-MM`: move an event on a certain date to another time
    - `YYYY-MM-DD->YYYY-MM-DD HH:MM-HH-MM`: move an event on a certain date to another date and time

The whole structure is quite unforgiving by design (meaning that if you make a typo or another mistake it, it will throw an error, rather than silently ignore it). For instance, if you have an unknown top-level key (e.g. `canceled`, rather than the UK spelling `cancelled`), Hugo compilation will crash and allow you to fix the event.
Also if you try to cancel an event on `2022-05-05`, even though there is no rule that generates an event for that day, compilation will fail.
All this should mean that typos in the structure should be easy to catch and fix.

Note that all crashing will happen during *building* of the site.
The end user will only ever see the static HTML, so will never see the error.
{: .notice}

In this system each `periodic` always has a start and end date.
This may feel not-ideal with events that last "forever" (such as the picnic, every last Friday of the month, until (at least) the [heat death of the Universe](https://en.wikipedia.org/wiki/Heat_death_of_the_universe)).
However since we need to generate a list of all events in order to show on the event page, we need to end up with a finite list.
Rather than implicitly using a 5 or 10 year limit, we allow you to set the limit.
Be advised though that if you set the `end` to `31-12-9999`, it will slow down the rending of your page; this might be fine if you have 1 or 2 event pages, maybe less so if you have 1000 pages.
I would personally advise to set this date to the end of next year (e.g. in 2023, you set it to `2025-01-01`).
Then once a year you search through your code for `2025-01-01`, and update all those that need another year.

A future version of this code might take a global "enddate" variable, and allow you to set `end` to something like `$global.calendar_enddate`, meaning you would only have to change this in one spot.
For now though, you will have to do this manually.
{: .notice--info}

The `eventDates` dictionary can be put in the front-matter of the page in question, or any other spot you like to keep it (e.g. in `/data` if that works in your case).

Hugo doesn't have custom functions, so in order to isolate the code that deals with this dictionary, we have to write code in (a definitely less developer-friendly) Go Template format, and save it in a *partial* (in our case, it's in `/layouts/partials/GetEventsFromEventsDates.html`, so this path will be used in the examples).
At the bottom of this post, you will find this *partial* code.

NOTE: all code shown in this article works on Hugo 0.106.0; it will probably work on other versions, but this has not been tested.
{: .notice--warning}

A *partial* can only be called in a *template* (not from markdown); which is (in our case) also exactly where we want it. In `/layouts/events/single.html` we include the following line (getting the `eventDates` from the page's front-matter):
```go
{% raw %}{{$events := partial "getEventsFromEventDates" (dict
    "timezone" "Europe/Warsaw"
    "eventDates" .Params.eventDates) }}{% endraw %}
```
This results is an `$events` variable with the following fields (note: boolean fields may be missing, in which case they should be assumed to be `false`):
- `startDateTime`: Hugo `Time` object (containing both a date and a time)
- `endDateTime`: Hugo `Time` object (containing both a date and a time)
- `cancelled`: Events from rules that are cancelled are still included in this list, it's up to the code rendering this whether to show these events (with a "cancelled" message) or not.
- `source`: one of `rule`, `rule+change`, `extra`; which part of the `eventDates` dictionary created this event
- `dateChanged`: True if the date was changed (through an entry in the `changed` key)
- `timeChanged`: True if the time was changed (through an entry in the `changed` key). Note that both `dateChanged` and `timeChanged` can be true at the same time
- `comment`: The comment for this event; this key may be missing if there is no comment.

At the bottom there is some example code on how to use this result, however this code is obviously easy to adjust to whatever you need.

## Download events as iCalendar (`.ics`) format

Wouldn't it be amazing if visitors could import the events into their own calendar? Luckily there is a format for this: [iCalendar](https://icalendar.org/) (this iCalendar standard should not be confused with the [Apple Calendar app, which used to be called iCal](https://en.wikipedia.org/wiki/Calendar_(Apple))).

Hugo already has support for iCalendar (`.ics`)-files, so generating them is only a couple of lines:
- Add a file `/layouts/events/single.ics` (may be as simple for now as "Hello World!"; at the bottom of this post there is a real-life example, which results in an `.ics` file with one entry per event).
- Add to the page's front-matter the following code (you can also set this globally in `config.toml`, but I haven't gotten that to work yet):

```yaml
outputs:
- html
- calendar
```

This should be enough to generate an `index.ics` file in the same directory as the `index.html` file for this page.

A link to this file can be made (in the `single.html` page) with this code: 
```go
{% raw %}<a href="{{(.OutputFormats.Get "Calendar").RelPermalink | absURL}}">...</a>{% endraw %}
```

Clicking this link downloads the `.ics` file, and opens it in your calendar app (giving you the option to import all events); I tested this in Apple Calendar, but supposedly also works in Microsoft Outlook (for Google Calendar [follow these instructions](https://support.google.com/calendar/answer/37118?hl=en&co=GENIE.Platform%3DDesktop)).


## Bonus: subscribe to the iCalendar (`.ics`) file

Actually, when you get to this part, you get the bonus for free :).
Rather that just downloading and importing the `.ics` file, you can also *subscribe to the calendar*.
This means that not only you get all events in your calendar app, but any change will also sync to the app (usually the app allows you to select how often you want to sync; since a user will just download a static file at this time from your webserver, it shouldn't be too much load, but you're response to do the math (e.g. 10k users, downloading every 15 minutes a 1MB `.ics` file (which is huge, but easily creatable using rules), *will be* 30TB of data transfer per month).

There is actually a [`REFRESH-INTERVAL` property](https://icalendar.org/New-Properties-for-iCalendar-RFC-7986/5-7-refresh-interval-property.html) in RFC 7986, which supposedly one could use to make a suggestion on how often the calendar should be re-downloaded, but this property was ignored by Apple Calendar.
{: .notice}

In Apple Calendar (version 11.0), you can subscribe to a calendar using `File -> New Calendar Subscription...`.
If on this point you fill in the url of the `.ics` file, and on the next page choose a name and a refresh interval for the calendar (I have been unable to fill these with default values from the `.ics` file, if you have better luck, please leave a comment!), you will see a new calendar in your side-bar, both on your mac, and (after a small wait) on your iPhone/iPad.

Unfortunately I have not been able yet to start the "Subscribe to calendar" process from the webpage.
A link to the `.ics` file on the webpage, opens the calendar events for import in Apple Calendar.
When I change the protocol for the download link to `webcal://` instead of `http(s)://`, it opens the "Subscribe" dialog in Apple Calendar, but will then try to talk the webcal protocol to my server (which doesn't work).
If someone finds a solution for this, I would love to hear it!

Subscribing to a calendar is (afaik) also possible in Outlook and Google Calendar, as well as in most other calendar software; it should be easy enough to search for instructions for your favourite tool.
{: .notice}

## Sneak peek: `list` and `taxonomy` pages

Obviously on the `list` page we want a calendar overview with all events (*and* an `.ics` download file with all events).
Getting all events is relatively easy:

```go
{% raw %}{{ $allPages := where (where .Site.AllPages "Type" "==" $.Page.Type) "Kind" "page" }}
{{ $s := newScratch }}
{{ range $allPages }}
    {{if .Params.eventDates -}}
        {{- $events := partial "getEventsFromEventDates" (dict "timezone" "Europe/Warsaw" "eventDates" .Params.eventDates) }}
        {{ $s.Add "events" $events }}
    {{ end }}
{{ end }}{% endraw %}
```

Obviously some more work will have to be done afterwards (like sorting, and then deciding how to show them), but that shouldn't be too hard.

Something similar can be done for tags pages (*taxonomy* pages in Hugo), meaning you could generate a subscribable calendar for the tag "Workshops" or "Social Events".

## Other future developments
There are a couple of things that we still have on our wishlist:
- Some javascript to make sure that on the event-page you will see those events you're most interested in.
- How to deal with multi-lingual pages -- there are some event pages that exist both in UK and PL languages, and obviously you don't want to keep the same list of eventsDates in both front-matters.
- How to deal with updates (i.e. an event organiser may want to change an event at short notice. Right now that would involve making a pull request for the website, then finding someone to approve it, merge it, check how it looks, deploy online. It might be acceptable initially (as in: even this is better than the current situation), but down the line this will need to be automated a bit.)



## Code

### Partial
<figure markdown="1">
```go
{% raw %}{{/*
Wants a dict as context, with the following keys:
- eventDates: The eventdates dict. This dict has 4 optional keys:
    - periodics: list of dicts with keys:
        - start: the start-date (YYYY-MM-DD) for the period that this periodic is active
        - end: the end-date (YYYY-MM-DD) for this period. The range is EXCLUDING this date
        - rule: The rule defining which days in this period the event is happening
            - "(1) (2) of the month" (e.g. "last Friday of the month")
                - (1) is one of "first|second|third|fourth|fifth|last|penultimate"
                - (2) is one of the names of the days of the week in English
            - "every X days" (e.g. every 14 days)
        - starttime: the time (HH:MM) at which the event starts in this period
        - endtime: the time (HH:MM) at which the event ends in this period
        - comment (optional): default comment for this event
- timezone: The timezone in which 


returns a list of dicts with keys (note that boolean keys may be missing if false):
    - startDateTime: time.Time in the given timezone
    - endDateTime: time.Time in the given timezone. Note that if endtime < starttime, the enddate is going to be startdate + 1
    - cancelled: true if cancelled
    - source: one of "rule", "rule+change", "extra"
    - dateChanged: true if rule+change and the date was changed
    - timeChanged: true if rule+change and the time was changed
    - comment: comment for this event, or missing

The result it sorted by startDateTime of the event.


Known limitations:
- If the periodics work so that there are multiple events on the same day, the latter event will overwrite the former one.

*/}}

{{ define "partials/GetStartEndDateTime.html" }}
    {{ $date := .date }}{{/* Date object */}}
    {{ $start := .start }}{{/* eg "18:00" */}}
    {{ $end := .end }}{{/* eg "18:00" */}}
    {{ $starttimesplit := split $start ":" }}
    {{ $starthours := int (index $starttimesplit 0 ) }}
    {{ $startminutes := int (index $starttimesplit 1 ) }}
    {{ $startdatetime := $date.Add (time.ParseDuration (printf "%dh%dm" $starthours $startminutes)) }}
    {{ $endtimesplit := split $end ":" }}
    {{ $endhours := int (index $endtimesplit 0 ) }}
    {{ $endminutes := int (index $endtimesplit 1 ) }}
    {{ $enddatetime := $date.Add (time.ParseDuration (printf "%dh%dm" $endhours $endminutes)) }}
    {{ $enddatetime := $enddatetime.AddDate 0 0 (cond (lt $enddatetime $startdatetime) 1 0) }}
    {{ return (dict "startDateTime" $startdatetime "endDateTime" $enddatetime) }}
{{ end }}

{{ $TIMEZONE := .timezone }}
{{ $ORDINAL_LOOKUP := dict
    "first" 1
    "second" 2
    "third" 3
    "fourth" 4
    "fifth" 5
    "last" -1
    "penultimate" -2}}
{{ $WEEKDAYS_LOOKUP := dict
    "Sunday" 0
    "Monday" 1
    "Tuesday" 2
    "Wednesday" 3
    "Thursday" 4
    "Friday" 5
    "Saturday" 6
}}
{{ $DAYS_IN_WEEK := 7 }}
{{ $ALLOWED_TOPLEVEL_KEYS := dict
    "periodics" false
    "cancelled" false
    "extra" false
    "changes" false
}}
{{ $ALLOWED_PERIODIC_KEYS := dict
    "start" true
    "end" true
    "rule" true
    "starttime" true
    "endtime" true
    "comment" false
}}

{{/* extra keys check */}}
{{ range $key, $value := .eventDates }}
    {{if not (isset $ALLOWED_TOPLEVEL_KEYS $key)}}
        {{ errorf "Key \"%s\" not allowed in eventDates" $key }}
    {{end}}
{{ end }}

{{ $s := newScratch }}

{{ range .eventDates.periodics }}
    {{ range $key, $value := . }}
        {{if not (isset $ALLOWED_PERIODIC_KEYS $key)}}
            {{ errorf "Key \"%s\" not allowed in periodics" $key }}
        {{end}}
    {{ end }}
    {{ $periodic := . }}
    {{ $start := time .start $TIMEZONE }}
    {{ $end := time .end $TIMEZONE }}
    {{ $seconds := (sub $end.Unix $start.Unix) }}
    {{/* Add 2 hours to compensate for DLS, then divide by seconds per day */}}
    {{ $nrdays := (div (add $seconds 7200) (mul 3600 24)) }}
    {{ $comment := .comment }}
    {{ if (findRE `^(first|second|third|fourth|fifth|last|penultimate) (Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday) of the month$` .rule) }}
        {{ $ruleparts := split .rule " " }}
        {{ $times := index $ruleparts 5 }}
        {{ $ordinal := index $ORDINAL_LOOKUP (index $ruleparts 0) }}
        {{ $weekday := index $WEEKDAYS_LOOKUP (index $ruleparts 1) }}
        {{ $diffdays_other_month := int (mul -7 $ordinal) }}
        {{ $diffdays_same_month := int (add $diffdays_other_month (cond (lt $diffdays_other_month 0) 7 -7)) }}
        {{ $startday_offset := mod (add (sub $weekday $start.Weekday) $DAYS_IN_WEEK) $DAYS_IN_WEEK }}
        {{ range $i := (seq $startday_offset $DAYS_IN_WEEK (sub $nrdays 1)) }}
            {{ $date := $start.AddDate 0 0 $i }}
            {{ if (and
                ( ne $date.Month ($date.AddDate 0 0 $diffdays_other_month).Month)
                ( eq $date.Month ($date.AddDate 0 0 $diffdays_same_month).Month)
                ) }}
                {{/* todo what if already exists? For now we don't care */}}
                {{ $startEndDT := partial "GetStartEndDateTime" (dict "date" $date "start" $periodic.starttime "end" $periodic.endtime) }}
                {{ $s.SetInMap "events" ($date.Format "2006-01-02") (merge $startEndDT (dict "source" "rule" "comment" $comment )) }}
            {{ end }}
        {{ end }}
    {{ else if (findRE `^every \d+ days$` .rule) }}
        {{ $ruleparts := split .rule " " }}
        {{ $interval := int (index $ruleparts 1) }}
        {{ range (seq 0 $interval (sub $nrdays 1)) }}
            {{ $date := $start.AddDate 0 0 . }}
            {{ $startEndDT := partial "GetStartEndDateTime" (dict "date" $date "start" $periodic.starttime "end" $periodic.endtime) }}
            {{ $s.SetInMap "events" ($date.Format "2006-01-02") (merge $startEndDT (dict "source" "rule" "comment" $comment)) }}
        {{ end }}
    {{ else }}
        {{ errorf "Don't understand rule \"%s\""  .rule }}
    {{ end }}
{{ end }}

{{ range $key, $value := .eventDates.cancelled }}
    {{ if not (isset ($s.Get "events") $key) }}
        {{ errorf "Trying to cancel event on %s but no such event" $key }}
    {{ end }}
    {{ $s.SetInMap "events" $key (merge (index ($s.Get "events") $key) (dict "cancelled" true)) }}
{{ end }}

{{ range $key, $value := .eventDates.extra }}
    {{ $splitkey := split $key " " }}
    {{ $date := time (index $splitkey 0) $TIMEZONE}}
    {{ $splittime := split (index $splitkey 1) "-" }}
    {{ $starttime := index $splittime 0 }}
    {{ $endtime := index $splittime 1 }}
    {{ $datestring := $date.Format "2006-01-02" }}
    {{ if isset ($s.Get "events") $datestring }}
        {{ errorf "Trying to plan extra event on %s but already an event" $key }}
    {{ end }}
    {{ $startEndDT := partial "GetStartEndDateTime" (dict "date" $date "start" $starttime "end" $endtime) }}
    {{ $s.SetInMap "events" $datestring (merge $startEndDT (dict "comment" $value "source" "extra")) }}
{{ end }}

{{ range $key, $value := .eventDates.changes }}
    {{/* TODO some regex to check it has the right format */}}
    {{ $splitkey := split $key "->" }}
    {{ $from := index $splitkey 0 }}
    {{ $changes := newScratch }}
    {{ $changes.Set "c" dict }}
    {{ $changes.Set "t" dict }}
    {{ $changes.SetInMap "c" "comment" $value }}
    {{ if eq (len $splitkey) 1 }}
        {{/* do nothing, since the comment is already set */}}
    {{ else }}
        {{ $to := index $splitkey 1 }}
        {{ $splitto := split $to " " }}

        {{ if eq (len $splitto) 2 }}
            {{ $changes.SetInMap "t" "date" (time (index $splitto 0)) }}
            {{ $changes.SetInMap "c" "dateChanged" true }}
            {{ $splittime := split (index $splitto 1) "-" }}
            {{ $starttime := index $splittime 0 }}
            {{ $endtime := index $splittime 1 }}
            {{ $changes.SetInMap "t" "start" $starttime }}
            {{ $changes.SetInMap "t" "end" $endtime }}
            {{ $changes.SetInMap "c" "timeChanged" true }}
        {{ else }}
            {{ if eq (len (split $to "-")) 2 }}
                {{ $splittime := split $to "-" }}
                {{ $starttime := index $splittime 0 }}
                {{ $endtime := index $splittime 1 }}
                {{ $changes.SetInMap "t" "start" $starttime }}
                {{ $changes.SetInMap "t" "end" $endtime }}
                {{ $changes.SetInMap "c" "timeChanged" true }}
            {{ else }}
                {{ $changes.SetInMap "t" "date" (time (index $splitto 0) $TIMEZONE) }}
                {{ $changes.SetInMap "c" "dateChanged" true }}
            {{ end }}
        {{ end }}
    {{ end }}
    {{ if not (isset ($s.Get "events") $from) }}
        {{ errorf "Trying to change event on %s but no such event" $key }}
    {{ end }}
    {{ $map := index ($s.Get "events") $from }}
    {{ $s.DeleteInMap "events" $from }}
    {{ $changes.SetInMap "c" "source" "rule+change" }}
    {{ $newDateAndTimes := (merge (dict "date" (time $from $TIMEZONE) "start" ($map.startDateTime.Format "15:04") "end" ($map.endDateTime.Format "15:04")) ($changes.Get "t")) }}
    {{ $startEndDT := partial "GetStartEndDateTime" $newDateAndTimes }}
    {{ $map := merge $map ($changes.Get "c") $startEndDT }}
    {{ $s.SetInMap "events" ($map.startDateTime.Format "2006-01-02") $map }}
{{ end }}

{{range $s.GetSortedMapValues "events"}}
    {{ $s.SetInMap "return" (.startDateTime.Format "2006-01-02T15:04:05") . }}
{{end}}

{{ return ($s.GetSortedMapValues "return") }}{% endraw %}
```
<figcaption markdown="1">
The partial (`/layouts/partials/GetEventsFromEventsDates.html`) necessary to convert the `eventDates` dictionary into a list of event dates, ready for rendering. For License, [see below](#license).
</figcaption>
</figure>

### HTML template
<figure markdown="1">
```go
{% raw %}{{if .Params.eventDates }}
{{$events := partial "GetEventsFromEventDates" (dict "timezone" "Europe/Warsaw" "eventDates" .Params.eventDates) }}
<div id="eventDates">
<ol>
{{ $s := newScratch }}
{{ $s.Set "year" "" }}
{{ range $key, $value := $events }}
    {{ if ne ($s.Get "year") $value.startDateTime.Year }}
    {{ if ne ($s.Get "year") "" }}</ol></li>{{end}}
        {{ $s.Set "year" $value.startDateTime.Year }}
        <li>{{ $s.Get "year" }}<ol>
    {{ end }}
    <li class="{{if $value.cancelled}}cancelled{{end}}">
        <span class="date{{if $value.dateChanged}} changed{{end}}">
            {{ time.Format "Monday, 2 January 2006" $value.startDateTime}}
        </span>
        <span class="time{{if $value.timeChanged}} changed{{end}}">
            {{ $value.startDateTime.Format "15:04" }}-{{ $value.endDateTime.Format "15:04" }}
        </span>
        {{if or $value.comment $value.cancelled}}: {{end}}
        {{if $value.cancelled}}<span class="cancelled">CANCELLED</span>{{end}}
        {{if $value.comment}}<span class="comment">{{ $value.comment }}</span>{{end}}
    </li>
{{end}}
{{ if ne ($s.Get "year") "" }}</ol></li>{{end}}
</ol>
<a href="{{(.OutputFormats.Get "Calendar").RelPermalink | absURL}}">Download this calendar</a>
</div>
{{ end }}{% endraw %}
```
<figcaption markdown="1">
The code in `layouts/events/single.html`, showing the events as seen in the example. Obviously this can be customized onto how you want it. For License, [see below](#license).
</figcaption>
</figure>

### iCalendar template
<figure markdown="1">
```
{% raw %}{{if .Params.eventDates -}}
{{- $events := partial "getEventsFromEventDates" (dict "timezone" "Europe/Warsaw" "eventDates" .Params.eventDates) }}
BEGIN:VCALENDAR
VERSION:2.0
PRODID:{{.Title}}
NAME:{{.Title}}
UID:{{.Permalink}}
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VTIMEZONE
TZID:Europe/Warsaw
X-LIC-LOCATION:Europe/Warsaw
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE
{{range $events}}
BEGIN:VEVENT
{{ with $.Params.organiser}}ORGANIZER;CN="{{ .name }}":mailto:{{ .email }}{{ end }}
SUMMARY:{{if .cancelled}}CANCELLED: {{end}}{{$.Title}}{{with .comment}} -- {{.}}{{end}}
UID:{{dateFormat "20060102T150405" .startDateTime}}@hs3.pl
SEQUENCE:0
STATUS:{{if .cancelled}}CANCELLED{{else}}CONFIRMED{{end}}
DTSTAMP:{{dateFormat "20060102T150405" .startDateTime}}
DTSTART:{{dateFormat "20060102T150405" .startDateTime}}
DTEND:{{dateFormat "20060102T150405" .endDateTime}}
LOCATION:TBD
URL:{{.Permalink}}
END:VEVENT
{{end}}
END:VCALENDAR
{{end}}{% endraw %}
```
<figcaption markdown="1">
The `/layouts/events/single.ics` file.  There is a whole bunch of information about timezones which should probably be different if you're not in Central European Time. Also it assumes that an `organiser` with a `name` and `email` object in the page's front-matter. For License, [see below](#license).
</figcaption>
</figure>

## License
All code on this page falls under the [Creative Commons Attribution 4.0 International licensed](https://creativecommons.org/licenses/by/4.0/).
If you find this code useful however, it would be much appreciated if you left a comment, or get in touch in some other way mentioned on the homepage.

---
layout: default
title: Home
---

# Area Pulse

_Tracking Nigeria's political, economic, and tech discourse._

## Latest Posts

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ site.baseurl }}{{ post.url }}">{{ post.title }}</a> - {{ post.date | date: "%b %d, %Y" }}
    </li>
  {% endfor %}
</ul> 
# All-anonymous-IRC
Even in the 21st century, I still believe the pure art of communication found in IRC is unmatched by modern social media.

Just imagine: on some obscure corner of the internet, you and a group of people from all corners of the globe, arriving for various reasons. No account, no password, no authentication whatsoever – you were simply you. And there, you could simply enjoy pure communication (though I understand, of course, that unregulated services often devolve into rampant hostility and abusive language). To me, this is a beautiful ideal, full of art and a strong sense of nostalgia.

However, I must also admit that modern social media, in virtually every aspect, has almost entirely surpassed this archaic means of communication like IRC. It's an obsolete technology, I concede. But... couldn't we still, in this era of powerful modern advancements, re-experience some of that old charm? Furthermore, I believe IRC still holds significant potential, especially for lightweight applications.

## What is All-anonymous-IRC？

It's a real-time chat version similar to 4chan, 2chan, or other anonymous imageboards/forums. It retains traditional channels and private messaging (PM) functionality. It fully adheres to the concept of "complete anonymity, no roles, and no registration."

You don't need any registered account, nor do you need to log in. There's nothing else you need to do. All you need to do is connect to the server, select a channel, and start sending messages. It's that simple.

To maintain basic order, we've also implemented some basic administrative features. These include functionalities like administrators and channel passwords. We plan to introduce more updates later.

Because our design philosophy doesn't allow for "roles," many features requiring administrative control will require you to remember passwords carefully.

That's it. Simple as that.

## Quick Start！

### Server-side

- lease download Server.py and config.py to the same directory.

- Make sure to install the necessary Python dependencies beforehand.

- In config.py, configure the port, IP address, administrator password, server name, etc. (We generally don't recommend changing the version information).

- Then, in your terminal, run (two choose one):

  ```
  python server.py
  ```

  ```
  python3 server.py
  ```

- You'll know the server is running successfully when you see output similar to: [INFO] 服务器正在 ('0.0.0.0', 6667) 上运行... (or similar output indicating the server is active).

- We plan to create a packaged version once the project matures.

### Client-side[Same as GUI-Client]

- Please note: The current client is a test version designed for testing the server. We plan to develop a modern, packaged version with a GUI once the project matures.

- Simply download Client.py. At the beginning of the file, configure the IP address and port where the Server.py is running.

- Then, in your terminal, run (two choose one):

  ```
  python client.py
  ```

  ```
  python3 client.py
  ```

- You'll know the connection is successful when you are prompted to enter a username.

## About KaguyaIRC (yes, that's what I like to call it) 0.7

In this version, we've implemented quite a few new things, hoping to make this old beast look a bit more usable.

First off, channel permissions have been completely re-architected. If you've never encountered the concept of ONLY_ADMIN_CHANGE_TOPIC, then frankly, that's fantastic. Above all, our design prioritizes user equality and complete anonymity. Therefore, if you create a channel, there's only one way to manage it: memorize the password it gives you upon creation. What if you leave the server and come back? No worries – just use the password to regain your privileges. Remember this: permissions are for *managing*, not for flaunting your identity or anything else. Arrogance will always come back to bite you. Your ability to manage is defined by your actions, not your status. Hence, not many will truly *need* this power. You wouldn't leak it, would you?

It might sound a bit unreasonable, but... this is actually the most logical aspect of the design. You're still you, just with a password. And don't worry, the password vanishes with the channel itself. So often, it's gone before it even has a chance to be compromised.

On a similar note, we've finally added kick and ban functionalities. Channel owners can manage within their respective channels, while server administrators can manage not only channels but also overall server privileges.

Of course, most people's IPs are dynamic nowadays, so who we're actually banning is anyone's guess, and who *you* are after your next login is equally a mystery. But hey, it doesn't matter. Who cares *who* you are? If we did, you wouldn't be here in the first place.

So, that's KaguyaIRC 0.7. I'm genuinely excited to see what it evolves into once it hits 1.0.

## DevStack

- Python 3.13

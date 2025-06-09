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

### Client-side

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

## DevStack

- Python 3.13

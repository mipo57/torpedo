FROM osminogin/tor-simple

USER root
RUN sed -i '1s/^/ControlPort 0.0.0.0:9051\n/' /etc/tor/torrc
RUN sed -i '1s/^/HashedControlPassword 16:529C61A2AD44976F6082D8D663F4E25989B85D39373366AB506F458383\n/' /etc/tor/torrc
RUN sed -i '1s/^/CookieAuthentication 1\n/' /etc/tor/torrc


USER tor
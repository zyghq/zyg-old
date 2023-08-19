class SlackConnectorAPI:
    def send_message(self, channel, message):
        print(f"Sending message to {channel.channel_id}: {message}")

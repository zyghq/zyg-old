CREATE_ISSUE_TEMPLATE_BLOCK = """
{
	"blocks": [{
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": ":red_circle: {{status}}",
				"emoji": true
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": ":ticket: <https://example.com|*Issue #{{issue_number}}*>"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "_<@U03NGJTT5JT> In <#C05KPPM03T8> | 9 Sept 2023 at 11:08 AM_"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "{{text|safe}}"
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "context",
			"elements": [{
					"type": "mrkdwn",
					"text": "Requester: *<@U03NGJTT5JT>*"
				},
				{
					"type": "mrkdwn",
					"text": "*Unassigned*"
				},
				{
					"type": "mrkdwn",
					"text": "Priority: *{{priority}}*"
				}
			]
		},
		{
			"type": "actions",
			"elements": [{
				"type": "button",
				"text": {
					"type": "plain_text",
					"text": "Claim",
					"emoji": true
				},
				"style": "primary",
				"value": "click_me_123",
				"action_id": "actionId-0"
			}]
		}
	]
}
"""

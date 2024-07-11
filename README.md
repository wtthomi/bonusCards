# BonusCard Software
- Stores give out Cards with QR Codes
- Links are built like this: https://[HOSTNAME]/testCard?card_id=XXX
- This Endpoint reroutes Users to their correct endpoint.
  1.  This card_id isnt signed up yet: /signCard
  2.  This card_id is already signed up: /login, also with card_id as GET so it gets automatically typed in
  3.  An admin is logged in -> reroute to adminDashboard, with card id already typed in, so merchants can add points quicker
- Products to win are defined in winnings.json with name and points
## TODO:
- Give admins option to see winnings, add winnings and choose them for substraction
- Also let admins see at a glance how many points users have (for telling them)

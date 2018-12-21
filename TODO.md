### TODO LIST
- [x] make `suggestion` a dict and add reason for suggestion
- [x] order quantity be half (or some percentage) of current shares of holding
- [x] log suggestion
- [x] log the change of daily extremes (and the reason)
- [ ] do trade in extended hours correctly
- [ ] what does the price param in a market buy/sell order mean? use it correctly
    - is the price param required or optional
    - adding the price param may make the order similar to limit loss
- [ ] check available buying power before suggesting to buy (now we are check it right before buying)
- [ ] add more analysis rules (if needed)
    - change ALLOWED_SYMBOLS into a dict

- [ ] Build a simple dashboard website with LDAP access control. Roadmap:
    - show a helloword page
    - add LDAP access control
    - show managed stocks symbol
    - able to turn on/off trading of each managed stock
- [ ] Improve the dashboard website (may postponed forever)
    - read log
    - show static daily price graph
    - show dynamic daily price graph





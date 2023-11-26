# pdKnockr
> A passive DNS "dive-by" tool

This tool is designed to detect passive DNS servers that are logging DNS queries by performing targeted subdomain lookups on a list of specified DNS resolvers. The core functionality of the program lies in its ability to generate unique subdomains using a seed value, ensuring that each query is distinct and traceable. This approach is particularly effective in identifying passive DNS servers, which typically log and store DNS queries for analysis and tracking purposes. By generating these unique queries, the tool can pinpoint which DNS resolvers are passively logging requests, a critical insight for network security analysis and privacy assessments.

The program operates by accepting a list of DNS resolver addresses and a seed value for subdomain generation. It then asynchronously queries each resolver with a dynamically generated subdomain, based on the provided seed, targeting a specific domain. The asynchronous nature of the tool allows for high-throughput and efficient querying, making it suitable for scanning a large number of resolvers in a short period. Users should note that while this tool provides valuable insights into DNS logging practices, it should be used responsibly and in compliance with applicable network and privacy regulations. It serves as a powerful instrument for network administrators, security researchers, and privacy advocates to understand and evaluate the extent of passive DNS logging in their networks or across various resolvers.

## WORK IN PROGRESS (STAY TUNED)

- Right now we can MASS query a subdomain on a domain or list of domains using a list of resolvers or the resolvers from public-dns.info
- Need to generate a seed per-dns server that can be included in the subdomain so it can be reversed back to a know which specific dns server is logging all dns requests.
- Subdomain should be entirely random, have to look into commonly seen subdomains, but something like:
    - de.220.ftp.domain.com 
    - astro.login.domain.net 
    - customer-cdn.1220.domain.org

Every sweep, we will generate a random seed for each dns server and save it to a seed.key file.

This is all very theoretical right now, interested to see how this pans out.
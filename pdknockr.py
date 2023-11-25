#!/usr/bin/env python
# Passive DNS Knocker (PDK) - developed by acidvegas in python (https://git.acid.vegas/pdknockr)

import asyncio
import random

try:
    import aiodns
except ImportError:
    raise SystemExit('missing required \'aiodns\' module (pip install aiodns)')


async def dns_lookup(domain: str, subdomain: str, dns_server: str):
    '''
    Perform a DNS lookup on a target domain.
    
    :param domain: The target domain to perform the lookup on.
    :param subdomain: The subdomain to look up.
    :param dns_server: The DNS server to perform the lookup on.
    '''
    domain = f'{subdomain}.{domain}'
    resolver = aiodns.DNSResolver(nameservers=[dns_server])
    try:
        answers = await resolver.query(domain, 'A')
        print(f'[\033[92mDONE\033[0m] Knocking \033[96m{domain}\033[0m on \033[93m{dns_server}\033[0m')
    except Exception as e:
        print(f'Error resolving {domain} using {dns_server}: {e}')


async def main(input_file: str, domains: str, subdomain: str, concurrency: int):
    '''
    Main function for the program.
    
    :param input_file: The file containing the list of domains to perform lookups on.
    :param domains: The comma seperated list of domains to perform lookups on.
    :param subdomain: The subdomain to look up.
    :param concurrency: The maximum number of concurrent lookups to perform.
    '''
    semaphore = asyncio.BoundedSemaphore(concurrency)

    if args.domains:
        domains = args.domains.split(',')
        async for domain in domains:
            for dns_server in dns_servers:
                await semaphore.acquire()
                asyncio.create_task(dns_lookup(domain, subdomain, dns_server, semaphore))

    elif args.input:
        async with asyncio.open_file(input_file, 'r') as file:
            async for domain in file:
                await semaphore.acquire()
                dns_server = random.choice(dns_servers)
                asyncio.create_task(dns_lookup(domain, subdomain, dns_server, semaphore))



if __name__ == '__main__':
    import argparse
    import os
    import urllib.request

    parser = argparse.ArgumentParser(description='Passive DNS Knocking Tool')
    parser.add_argument('-d', '--domains', help='Comma seperate list of domains')
    parser.add_argument('-i', '--input', help='File containing list of domains')
    parser.add_argument('-s', '--subdomain', help='Subdomain to look up')
    parser.add_argument('-c', '--concurrency', type=int, default=50, help='Concurrency limit')
    parser.add_argument('-r', '--resolvers', help='File containing list of DNS resolvers (uses public-dns.info if not specified)')
    args = parser.parse_args()

    if not args.input and not args.domain:
        raise SystemExit('no domains specified')
    
    if args.input and args.domain:
        raise SystemExit('cannot specify both domain and input file')
    
    if args.input and not os.path.exists(args.input):
        raise SystemExit('input file does not exist')
    
    if args.resolvers:
        if os.path.exists(args.resolvers):
            with open(args.resolvers, 'r') as file:
                dns_servers = [item.strip() for item in file.readlines() if item.strip()]
                if not dns_servers:
                    raise SystemExit('no DNS servers found in file')
                else:
                     print(f'Loaded {len(dns_servers):,} DNS servers from file')
        else:
            raise SystemExit('DNS servers file does not exist')
    else:
        dns_servers = urllib.request.urlopen('https://public-dns.info/nameservers.txt').read().decode().split('\n')
        print(f'Loaded {len(dns_servers):,} DNS servers from public-dns.info')

    asyncio.run(main(args.input, args.domain, args.subdomain, args.concurrency))
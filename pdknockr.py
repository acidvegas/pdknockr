#!/usr/bin/env python
# Passive DNS Knocker (PDK) - developed by acidvegas in python (https://git.acid.vegas/pdknockr)

import asyncio
import random

try:
    import aiodns
except ImportError:
    raise SystemExit('missing required \'aiodns\' module (pip install aiodns)')


async def dns_lookup(domain: str, subdomain: str, dns_server: str, dns_type: str, semaphore: asyncio.Semaphore):
    '''
    Perform a DNS lookup on a target domain.
    
    :param domain: The target domain to perform the lookup on.
    :param subdomain: The subdomain to look up.
    :param dns_server: The DNS server to perform the lookup on.
    '''
    async with semaphore:
        target = f'{subdomain}.{domain}'
        resolver = aiodns.DNSResolver(nameservers=[dns_server])
        try:
            await resolver.query(target, dns_type)
            print(f'[\033[92mDONE\033[0m] Knocking \033[96m{target}\033[0m on \033[93m{dns_server}\033[0m')
        except Exception as e:
            print(f'[\033[31mFAIL\033[0m] Knocking \033[96m{target}\033[0m on \033[93m{dns_server}\033[0m \033[90m({e})\033[0m')


async def main(args):
    '''
    Main function for the program.
    
    :param args: The arguments passed to the program.
    '''
    global dns_servers

    semaphore = asyncio.BoundedSemaphore(args.concurrency)
    tasks = []

    if args.domains:
        for domain in args.domains.split(','):
            for dns_server in dns_servers:
                if len(tasks) < args.concurrency:
                    task = asyncio.create_task(dns_lookup(domain, args.subdomain, dns_server, args.rectype, semaphore))
                    tasks.append(task)
                else:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = list(pending)

    elif args.input:
        async with asyncio.open_file(args.input, 'r') as file:
            for domain in file:
                for dns_server in dns_servers:
                    if len(tasks) < args.concurrency:
                        task = asyncio.create_task(dns_lookup(domain, args.subdomain, dns_server, args.rectype, semaphore))
                        tasks.append(task)
                    else:
                        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                        tasks = list(pending)



if __name__ == '__main__':
    import argparse
    import os
    import urllib.request

    parser = argparse.ArgumentParser(description='Passive DNS Knocking Tool')
    parser.add_argument('-d', '--domains', help='Comma seperate list of domains')
    parser.add_argument('-i', '--input', help='File containing list of domains')
    parser.add_argument('-s', '--subdomain', help='Subdomain to look up')
    parser.add_argument('-c', '--concurrency', type=int, default=50, help='Concurrency limit (default: 50)')
    parser.add_argument('-r', '--resolvers', help='File containing list of DNS resolvers (uses public-dns.info if not specified)')
    parser.add_argument('-rt', '--rectype', default='A', help='DNS record type (default: A)')
    args = parser.parse_args()

    if not args.input and not args.domains:
        raise SystemExit('no domains specified')
    
    elif args.input and args.domains:
        raise SystemExit('cannot specify both domain and input file')
    
    elif args.input and not os.path.exists(args.input):
        raise SystemExit('input file does not exist')

    elif args.rectype and args.rectype not in ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT']:
        raise SystemExit('invalid record type')
    
    elif args.resolvers:
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

    asyncio.run(main(args))
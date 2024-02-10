#!/usr/bin/env python
# Passive DNS Knocker (PDK) - developed by acidvegas in python (https://git.acid.vegas/pdknockr)

import argparse
import asyncio
import logging
import logging.handlers
import os
import random
import time

try:
    import aiodns
except ImportError:
    raise SystemExit('missing required \'aiodns\' module (pip install aiodns)')


async def dns_lookup(semaphore: asyncio.Semaphore, domain: str, dns_server: str, record_type: str, timeout: int):
    '''
    Perform a DNS lookup on a target domain.
    
    :param domain: The target domain to perform the lookup on.
    :param subdomain: The subdomain to look up.
    :param dns_server: The DNS server to perform the lookup on.
    :param dns_type: The DNS record type to look up.
    :param timeout: The timeout for the DNS lookup.
    :param semaphore: The semaphore to use for concurrency.
    '''
    async with semaphore:
        resolver = aiodns.DNSResolver(nameservers=[dns_server], timeout=timeout)

        logging.info(f'Knocking {dns_server} with {domain} ({record_type})')

        try:
            await resolver.query(domain, record_type)
        except:
            pass # We're just knocking so errors are expected and ignored
        
        
def read_domain_file(file_path: str):
    '''
    Generator function to read domains line by line.
    
    :param file_path: The path to the file containing the DNS servers.
    '''
    with open(file_path, 'r') as file:
        while True:
            for line in file:
                line = line.strip()
                if line:
                    yield line


def read_dns_file(file_path: str):
    '''
    Generator function to read DNS servers line by line.
    
    :param file_path: The path to the file containing the DNS servers.
    '''
    with open(file_path, 'r') as file:
        while True:
            for line in file:
                line = line.strip()
                if line:
                    yield line


def generate_subdomain(sub_domains: list, domain: str, max_size: int):
    '''
    Generator function to read subdomains line by line.
    
    :param sub_domains: The list of subdomains to use for generating noise.
    '''
    while True:
        subs = random.sample(sub_domains, random.randint(2, max_size))

        if random.choice([True, False]):
            subs_index = random.randint(0, max_size - 1)
            subs[subs_index] = subs[subs_index] + str(random.randint(1, 99))

        yield random.choice(['.', '-']).join(subs) + '.' + domain


def setup_logging():
    '''Setup the logging for the program.'''

    os.makedirs('logs', exist_ok=True)

    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)9s | %(message)s', '%I:%M %p'))

    log_filename = time.strftime('pdk_%Y-%m-%d_%H-%M-%S.log')

    fh = logging.handlers.RotatingFileHandler(f'logs/{log_filename}', maxBytes=268435456, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)9s | %(message)s', '%Y-%m-%d %I:%M %p')) 

    logging.basicConfig(level=logging.NOTSET, handlers=(sh,fh))


async def main():
    '''Main function for the program.'''
    
    parser = argparse.ArgumentParser(description='Passive DNS Knocking Tool')
    parser.add_argument('-d', '--domains', help='Comma seperate list of domains or file containing list of domains')
    parser.add_argument('-s', '--subdomains', help='File containing list of subdomains')
    parser.add_argument('-r', '--resolvers', help='File containing list of DNS resolvers')
    parser.add_argument('-rt', '--rectype', default='A,AAAA', help='Comma-seperated list of DNS record type (default: A,AAAA)')
    parser.add_argument('-c', '--concurrency', type=int, default=25, help='Concurrency limit (default: 50)')
    parser.add_argument('-t', '--timeout', type=int, default=3, help='Timeout for DNS lookup (default: 3)')
    parser.add_argument('-n', '--noise', action='store_true', help='Enable random subdomain noise')
    args = parser.parse_args()
    
    setup_logging()
    
    args.rectype = [record_type.upper() for record_type in args.rectype.split(',')]
    
    if not args.domains:
        raise SystemExit('no domains specified')
    elif not os.path.exists(args.domains):
        raise FileNotFoundError('domains file not found')
    
    if not args.subdomains:
        raise SystemExit('no subdomains file specified')
    elif not os.path.exists(args.subdomains):
        raise FileNotFoundError('subdomains file not found')
    
    if not args.resolvers:
        raise SystemExit('no resolvers file specified')
    elif not os.path.exists(args.resolvers):
        raise FileNotFoundError('resolvers file not found')
    
    valid_record_types = ('A', 'AAAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT')

    for record_type in args.rectype:
        if record_type not in valid_record_types:
            raise SystemExit(f'invalid record type: {record_type}')
    
    semaphore = asyncio.BoundedSemaphore(args.concurrency)
    
    while True:
        tasks = []        

        for domain in read_domain_file(args.domains):

            for dns_server in read_dns_file(args.resolvers):
                sub_domain = generate_subdomain(args.subdomains, domain, 3)
                
                if len(tasks) < args.concurrency:
                    query_record = random.choice(args.record_types)
                    task = asyncio.create_task(dns_lookup(semaphore, domain, sub_domain, dns_server, query_record, args.timeout))
                    tasks.append(task)

                else:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = list(pending)
                    
        await asyncio.wait(tasks) # Wait for any remaining tasks to complete
                    
        if not args.noise:
            break



if __name__ == '__main__':
    asyncio.run(main())
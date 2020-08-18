import { mount } from '@vue/test-utils'

import clinFields from '../clin_fields'

import { makeTestWrapper } from '../../test_utils/component_test_helpers'

const ClinFieldsWrapper = makeTestWrapper({
  components: { clinFields },
  templatePath: 'clin_fields.html',
})

describe('ClinFields Test', () => {
  it('should calculate the percentage of obligated funds', async () => {
    const wrapper = mount(ClinFieldsWrapper, {
      propsData: {
        initialData: {},
      },
    })
    const percentObligatedElement = wrapper.find('#percent-obligated')
    // test starts at zero
    expect(percentObligatedElement.text()).toBe('0%')

    // test greater than 100%
    await wrapper.find('input#obligated_amount').setValue('2')
    await wrapper.find('input#total_amount').setValue('1')
    expect(percentObligatedElement.text()).toBe('>100%')

    // test greater than 99% but less than 100%
    await wrapper.find('input#obligated_amount').setValue('999')
    await wrapper.find('input#total_amount').setValue('1000')
    expect(percentObligatedElement.text()).toBe('>99%')

    // test a normal percentage
    await wrapper.find('input#obligated_amount').setValue('1')
    await wrapper.find('input#total_amount').setValue('2')
    expect(percentObligatedElement.text()).toBe('50%')

    // test less than 1%
    await wrapper.find('input#obligated_amount').setValue('1')
    await wrapper.find('input#total_amount').setValue('1000')
    expect(percentObligatedElement.text()).toBe('<1%')

    // test resets to zero
    await wrapper.find('input#obligated_amount').setValue('0')
    await wrapper.find('input#total_amount').setValue('0')
    expect(percentObligatedElement.text()).toBe('0%')
  })
})
